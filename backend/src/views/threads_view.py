from fastapi import UploadFile
from kink import inject
from starlette.requests import Request

from src.core.config import Settings
from src.core.exceptions import RateLimitedError
from src.core.storage import Storage
from src.schemas.thread import OpPostPreview, ThreadCreate, ThreadDetailResponse, ThreadResponse
from src.services.captcha_service import CaptchaService
from src.services.file_service import FileService
from src.services.thread_service import ThreadService
from src.utils.events import NEW_THREAD, EventPublisher, board_channel
from src.utils.rate_limit import RateLimiter
from src.views.dependencies import client_ip_hash
from src.views.serializers import post_response
from src.views.uploads import contains_image, read_uploads, store_uploads

THREAD_RATE_LIMIT = 3
THREAD_RATE_WINDOW = 60


class ThreadsView:
    @inject
    def __init__(
        self,
        thread_service: ThreadService,
        file_service: FileService,
        captcha_service: CaptchaService,
        rate_limiter: RateLimiter,
        events: EventPublisher,
        storage: Storage,
        settings: Settings,
    ) -> None:
        self.thread_service = thread_service
        self.file_service = file_service
        self.captcha_service = captcha_service
        self.rate_limiter = rate_limiter
        self.events = events
        self.storage = storage
        self.settings = settings

    async def list_threads(
        self, board_slug: str, limit: int = 50, offset: int = 0
    ) -> list[ThreadResponse]:
        thread_data = await self.thread_service.list_threads(board_slug, limit, offset)
        responses: list[ThreadResponse] = []
        for thread, op_post, first_image in thread_data:
            response = ThreadResponse.model_validate(thread)
            if op_post:
                thumbnail_url = (
                    self.storage.public_url(first_image.thumbnail_path)
                    if first_image and first_image.thumbnail_path
                    else None
                )
                response.op_post = OpPostPreview(
                    body=op_post.body,
                    thumbnail_url=thumbnail_url,
                )
            responses.append(response)
        return responses

    async def get_thread(self, board_slug: str, thread_id: int) -> ThreadDetailResponse:
        thread, posts, attachments_by_post = await self.thread_service.get_thread_detail(
            board_slug, thread_id
        )
        detail = ThreadDetailResponse.model_validate(thread)
        detail.posts = [
            post_response(post, attachments_by_post.get(post.id, []), self.storage)
            for post in posts
        ]
        return detail

    async def create_thread(
        self,
        board_slug: str,
        data: ThreadCreate,
        files: list[UploadFile],
        request: Request,
        captcha_token: str,
        captcha_answer: str,
    ) -> ThreadDetailResponse:
        ip_hash = client_ip_hash(request, self.settings)
        await self.captcha_service.validate(captcha_token, captcha_answer)
        if not await self.rate_limiter.is_allowed(
            f"thread:{ip_hash}", THREAD_RATE_LIMIT, THREAD_RATE_WINDOW
        ):
            raise RateLimitedError("too many threads, slow down")

        uploads = await read_uploads(files)
        thread, op_post = await self.thread_service.create_thread(
            board_slug, data, ip_hash, has_image=contains_image(uploads)
        )
        attachments = await store_uploads(self.file_service, op_post.id, uploads)

        detail = ThreadDetailResponse.model_validate(thread)
        detail.posts = [post_response(op_post, attachments, self.storage)]
        await self.events.publish(
            board_channel(board_slug), NEW_THREAD, detail.model_dump(mode="json")
        )
        return detail
