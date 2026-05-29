from kink import inject
from starlette.requests import Request

from src.core.config import Settings
from src.core.exceptions import RateLimitedError
from src.schemas.post import PostResponse
from src.schemas.thread import ThreadCreate, ThreadDetailResponse, ThreadResponse
from src.services.captcha_service import CaptchaService
from src.services.thread_service import ThreadService
from src.utils.rate_limit import RateLimiter
from src.views.dependencies import client_ip_hash

THREAD_RATE_LIMIT = 3
THREAD_RATE_WINDOW = 60


@inject
class ThreadsView:
    def __init__(
        self,
        thread_service: ThreadService,
        captcha_service: CaptchaService,
        rate_limiter: RateLimiter,
        settings: Settings,
    ) -> None:
        self.thread_service = thread_service
        self.captcha_service = captcha_service
        self.rate_limiter = rate_limiter
        self.settings = settings

    async def list_threads(
        self, board_slug: str, limit: int = 50, offset: int = 0
    ) -> list[ThreadResponse]:
        threads = await self.thread_service.list_threads(board_slug, limit, offset)
        return [ThreadResponse.model_validate(thread) for thread in threads]

    async def get_thread(self, board_slug: str, thread_id: int) -> ThreadDetailResponse:
        thread, posts = await self.thread_service.get_thread_detail(board_slug, thread_id)
        detail = ThreadDetailResponse.model_validate(thread)
        detail.posts = [PostResponse.model_validate(post) for post in posts]
        return detail

    async def create_thread(
        self,
        board_slug: str,
        data: ThreadCreate,
        request: Request,
        captcha_token: str,
        captcha_answer: str,
    ) -> ThreadResponse:
        ip_hash = client_ip_hash(request, self.settings)
        await self.captcha_service.validate(captcha_token, captcha_answer)
        if not await self.rate_limiter.is_allowed(
            f"thread:{ip_hash}", THREAD_RATE_LIMIT, THREAD_RATE_WINDOW
        ):
            raise RateLimitedError("too many threads, slow down")

        thread, _op_post = await self.thread_service.create_thread(board_slug, data, ip_hash)
        return ThreadResponse.model_validate(thread)
