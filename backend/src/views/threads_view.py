from fastapi import UploadFile
from kink import inject
from starlette.requests import Request

from src.core.config import Settings
from src.core.exceptions import RateLimitedError
from src.core.storage import Storage
from src.schemas.thread import (
    ImagePreview,
    LatestThreadResponse,
    OpPostPreview,
    ReplyPreview,
    ThreadCreate,
    ThreadDetailResponse,
    ThreadResponse,
)
from src.services.board_service import BoardService
from src.services.captcha_service import CaptchaService
from src.services.file_service import FileService
from src.services.post_service import post_is_editable
from src.services.thread_service import ThreadService
from src.tasks.search import embed_post
from src.utils.clock import utcnow
from src.utils.events import NEW_THREAD, EventPublisher, board_channel
from src.utils.online import OnlineTracker
from src.utils.rate_limit import RateLimiter
from src.views.dependencies import client_ip_hash
from src.views.serializers import is_media_hidden, post_response
from src.views.uploads import contains_image, read_uploads, store_uploads

THREAD_RATE_LIMIT = 3
THREAD_RATE_WINDOW = 60


class ThreadsView:
    @inject
    def __init__(
        self,
        thread_service: ThreadService,
        board_service: BoardService,
        file_service: FileService,
        captcha_service: CaptchaService,
        rate_limiter: RateLimiter,
        events: EventPublisher,
        storage: Storage,
        settings: Settings,
        online_tracker: OnlineTracker,
    ) -> None:
        self.thread_service = thread_service
        self.board_service = board_service
        self.file_service = file_service
        self.captcha_service = captcha_service
        self.rate_limiter = rate_limiter
        self.events = events
        self.storage = storage
        self.settings = settings
        self.online_tracker = online_tracker

    async def list_threads(
        self, board_slug: str, request: Request, limit: int = 50, offset: int = 0
    ) -> list[ThreadResponse]:
        await self.online_tracker.touch(client_ip_hash(request, self.settings), board_slug)
        thread_data = await self.thread_service.list_threads(board_slug, limit, offset)
        board = await self.board_service.get_board(board_slug)
        responses: list[ThreadResponse] = []
        for thread, op_post, op_images, replies in thread_data:
            response = ThreadResponse.model_validate(thread)
            if op_post:
                # drop images hidden by moderation so the catalog preview stays clean
                visible_images = [
                    image
                    for image in op_images
                    if not is_media_hidden(image.moderation_status, board.is_nsfw)
                ]
                first_image = visible_images[0] if visible_images else None
                thumbnail_url = (
                    self.storage.public_url(first_image.thumbnail_path or first_image.file_path)
                    if first_image
                    else None
                )
                response.op_post = OpPostPreview(
                    body=op_post.body,
                    body_html=op_post.body_html,
                    thumbnail_url=thumbnail_url,
                    width=first_image.width if first_image else None,
                    height=first_image.height if first_image else None,
                    images=[
                        ImagePreview(
                            url=self.storage.public_url(image.file_path),
                            thumbnail_url=self.storage.public_url(
                                image.thumbnail_path or image.file_path
                            ),
                            width=image.width,
                            height=image.height,
                        )
                        for image in visible_images
                    ],
                )
            response.last_replies = [
                ReplyPreview(
                    id=reply.id,
                    post_number=reply.post_number,
                    name=reply.name,
                    body=reply.body,
                    body_html=reply.body_html,
                    created_at=reply.created_at,
                )
                for reply in replies
            ]
            responses.append(response)
        return responses

    async def list_latest_threads(self, limit: int = 5) -> list[LatestThreadResponse]:
        latest = await self.thread_service.list_latest_threads(limit)
        nsfw_by_slug = {
            board.slug: board.is_nsfw for board in await self.board_service.list_boards()
        }
        responses: list[LatestThreadResponse] = []
        for thread, board_slug, first_image, last_reply in latest:
            thumbnail_url = (
                self.storage.public_url(first_image.thumbnail_path or first_image.file_path)
                if first_image is not None
                and not is_media_hidden(
                    first_image.moderation_status, nsfw_by_slug.get(board_slug, False)
                )
                else None
            )
            responses.append(
                LatestThreadResponse(
                    id=thread.id,
                    board_slug=board_slug,
                    title=thread.title,
                    reply_count=thread.reply_count,
                    bump_at=thread.bump_at,
                    created_at=thread.created_at,
                    thumbnail_url=thumbnail_url,
                    last_reply=ReplyPreview(
                        id=last_reply.id,
                        post_number=last_reply.post_number,
                        name=last_reply.name,
                        body=last_reply.body,
                        body_html=last_reply.body_html,
                        created_at=last_reply.created_at,
                    )
                    if last_reply
                    else None,
                )
            )
        return responses

    async def get_thread(
        self, board_slug: str, thread_id: int, request: Request
    ) -> ThreadDetailResponse:
        viewer_ip_hash = client_ip_hash(request, self.settings)
        now = utcnow()
        await self.online_tracker.touch(viewer_ip_hash, board_slug)

        thread, posts, attachments_by_post = await self.thread_service.get_thread_detail(
            board_slug, thread_id
        )
        board = await self.board_service.get_board(board_slug)

        detail = ThreadDetailResponse.model_validate(thread)
        responses = []
        for post in posts:
            response = post_response(
                post, attachments_by_post.get(post.id, []), self.storage, board.is_nsfw
            )
            response.can_edit = post_is_editable(post, viewer_ip_hash, now)
            responses.append(response)
        detail.posts = responses

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
        await self.online_tracker.touch(ip_hash, board_slug)
        await self.captcha_service.validate(captcha_token, captcha_answer)
        if not await self.rate_limiter.is_allowed(
            f"thread:{ip_hash}", THREAD_RATE_LIMIT, THREAD_RATE_WINDOW
        ):
            raise RateLimitedError("too many threads, slow down")

        uploads = await read_uploads(files)
        thread, op_post = await self.thread_service.create_thread(
            board_slug, data, ip_hash, has_image=contains_image(uploads)
        )
        if op_post.body:
            embed_post.delay(op_post.id)  # type: ignore[attr-defined]  celery task
        attachments = await store_uploads(self.file_service, op_post.id, uploads)

        board = await self.board_service.get_board(board_slug)
        detail = ThreadDetailResponse.model_validate(thread)
        detail.posts = [post_response(op_post, attachments, self.storage, board.is_nsfw)]
        await self.events.publish(
            board_channel(board_slug), NEW_THREAD, detail.model_dump(mode="json")
        )
        detail.posts[0].can_edit = True
        return detail
