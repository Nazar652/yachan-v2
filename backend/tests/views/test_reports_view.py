from unittest.mock import AsyncMock, MagicMock

from src.schemas.report import ReportCreate, ReportResponse
from src.views.reports_view import ReportsView
from tests.views._factories import report_ns, request_ns, settings_ns


async def test_create_report_delegates_and_maps():
    report_service = MagicMock()
    report_service.create_report = AsyncMock(return_value=report_ns())
    view = ReportsView(report_service=report_service, settings=settings_ns())

    result = await view.create_report("b", 10, ReportCreate(reason="spam"), request_ns())

    assert isinstance(result, ReportResponse)
    report_service.create_report.assert_awaited_once()
