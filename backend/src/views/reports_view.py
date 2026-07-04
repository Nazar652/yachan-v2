from kink import inject
from starlette.requests import Request

from src.core.config import Settings
from src.core.exceptions import RateLimitedError
from src.schemas.report import ReportCreate
from src.services.report_service import ReportService
from src.utils.rate_limit import RateLimiter
from src.views.dependencies import client_ip_hash

REPORT_RATE_LIMIT = 5
REPORT_RATE_WINDOW = 600


class ReportsView:
    @inject
    def __init__(
        self,
        report_service: ReportService,
        rate_limiter: RateLimiter,
        settings: Settings,
    ) -> None:
        self.report_service = report_service
        self.rate_limiter = rate_limiter
        self.settings = settings

    async def create_report(
        self, board_slug: str, post_number: int, data: ReportCreate, request: Request
    ) -> None:
        ip_hash = client_ip_hash(request, self.settings)

        if not await self.rate_limiter.is_allowed(
            f"report:{ip_hash}", REPORT_RATE_LIMIT, REPORT_RATE_WINDOW
        ):
            raise RateLimitedError("too many reports, slow down")

        await self.report_service.create_report(board_slug, post_number, data, ip_hash)
