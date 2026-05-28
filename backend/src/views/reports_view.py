from kink import inject
from starlette.requests import Request

from src.core.config import Settings
from src.schemas.report import ReportCreate, ReportResponse
from src.services.report_service import ReportService
from src.views.dependencies import client_ip_hash


@inject
class ReportsView:
    def __init__(self, report_service: ReportService, settings: Settings) -> None:
        self.report_service = report_service
        self.settings = settings

    async def create_report(
        self, board_slug: str, post_number: int, data: ReportCreate, request: Request
    ) -> ReportResponse:
        ip_hash = client_ip_hash(request, self.settings)
        report = await self.report_service.create_report(
            board_slug, post_number, data, ip_hash
        )
        return ReportResponse.model_validate(report)
