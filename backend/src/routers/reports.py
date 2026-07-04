from fastapi import APIRouter, Depends, Request

from src.bootstrap.container import get_dependency
from src.schemas.report import ReportCreate
from src.views.reports_view import ReportsView

router = APIRouter(prefix="/{board_slug}", tags=["reports"])


@router.post("/posts/{post_number}/report", status_code=204)
async def create_report(
    board_slug: str,
    post_number: int,
    data: ReportCreate,
    request: Request,
    view: ReportsView = Depends(lambda: get_dependency(ReportsView)),
) -> None:
    await view.create_report(board_slug, post_number, data, request)
