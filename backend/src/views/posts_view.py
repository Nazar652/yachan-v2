from fastapi import UploadFile
from kink import inject
from starlette.requests import Request

from src.core.config import Settings
from src.core.exceptions import RateLimitedError
from src.core.storage import LocalStorage
from src.schemas.post import PostCreate, PostEditCreate, PostEditResponse, PostResponse
from src.services.captcha_service import CaptchaService
from src.services.file_service import FileService
from src.services.post_service import PostService
from src.utils.events import NEW_POST, POST_EDITED, EventPublisher, thread_channel
from src.utils.rate_limit import RateLimiter
from src.views.dependencies import client_ip_hash
from src.views.serializers import post_response
from src.views.uploads import read_uploads, store_uploads

REPLY_RATE_LIMIT = 10
REPLY_RATE_WINDOW = 60


class PostsView:
    @inject
    def __init__(
        self,
        post_service: PostService,
        file_service: FileService,
        captcha_service: CaptchaService,
        rate_limiter: RateLimiter,
        events: EventPublisher,
        storage: LocalStorage,
        settings: Settings,
    ) -> None:
        self.post_service = post_service
        self.file_service = file_service
        self.captcha_service = captcha_service
        self.rate_limiter = rate_limiter
        self.events = events
        self.storage = storage
        self.settings = settings

    async def create_reply(
        self,
        board_slug: str,
        thread_id: int,
        data: PostCreate,
        files: list[UploadFile],
        request: Request,
        captcha_token: str,
        captcha_answer: str,
    ) -> PostResponse:
        ip_hash = client_ip_hash(request, self.settings)
        await self.captcha_service.validate(captcha_token, captcha_answer)
        if not await self.rate_limiter.is_allowed(
            f"reply:{ip_hash}", REPLY_RATE_LIMIT, REPLY_RATE_WINDOW
        ):
            raise RateLimitedError("too many posts, slow down")

        uploads = await read_uploads(files)
        post = await self.post_service.create_reply(board_slug, thread_id, data, ip_hash)
        attachments = await store_uploads(self.file_service, post.id, uploads)

        response = post_response(post, attachments, self.storage)
        await self.events.publish(
            thread_channel(thread_id), NEW_POST, response.model_dump(mode="json")
        )
        return response

    async def edit_post(
        self, board_slug: str, post_number: int, data: PostEditCreate, request: Request
    ) -> PostResponse:
        ip_hash = client_ip_hash(request, self.settings)
        post = await self.post_service.edit_post(board_slug, post_number, data, ip_hash)
        response = PostResponse.model_validate(post)
        await self.events.publish(
            thread_channel(response.thread_id), POST_EDITED, response.model_dump(mode="json")
        )
        return response

    async def get_post_history(
        self, board_slug: str, post_number: int
    ) -> PostEditResponse | None:
        edit = await self.post_service.get_post_history(board_slug, post_number)
        return PostEditResponse.model_validate(edit) if edit else None
