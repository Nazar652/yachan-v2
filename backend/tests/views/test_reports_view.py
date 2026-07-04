from unittest.mock import AsyncMock, MagicMock

import pytest
from src.core.exceptions import RateLimitedError
from src.schemas.report import ReportCreate
from src.views.reports_view import ReportsView
from tests.views._factories import report_ns, request_ns, settings_ns


def build(*, allowed=True):
    report_service = MagicMock()
    report_service.create_report = AsyncMock(return_value=report_ns())
    rate_limiter = MagicMock()
    rate_limiter.is_allowed = AsyncMock(return_value=allowed)
    view = ReportsView(
        report_service=report_service, rate_limiter=rate_limiter, settings=settings_ns()
    )
    return view, report_service


async def test_create_report_delegates():
    view, report_service = build()

    result = await view.create_report("b", 10, ReportCreate(reason="spam"), request_ns())

    assert result is None
    report_service.create_report.assert_awaited_once()


async def test_create_report_rate_limited():
    view, report_service = build(allowed=False)

    with pytest.raises(RateLimitedError):
        await view.create_report("b", 10, ReportCreate(), request_ns())
    report_service.create_report.assert_not_called()
