from fastapi import APIRouter, Depends, Request

from src.schemas.report import ReportCreate, ReportResponse
from src.views.reports_view import ReportsView

router = APIRouter(prefix="/{board_slug}", tags=["reports"])


def _view() -> ReportsView:
    return ReportsView()


@router.post("/posts/{post_number}/report", response_model=ReportResponse, status_code=201)
async def create_report(
    board_slug: str,
    post_number: int,
    data: ReportCreate,
    request: Request,
    view: ReportsView = Depends(_view),
) -> ReportResponse:
    return await view.create_report(board_slug, post_number, data, request)
