from fastapi import APIRouter, Depends, Request

from src.bootstrap.container import get_dependency
from src.schemas.stats import SiteStatsResponse
from src.views.stats_view import StatsView

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("", response_model=SiteStatsResponse)
async def get_site_stats(
    request: Request, view: StatsView = Depends(lambda: get_dependency(StatsView))
) -> SiteStatsResponse:
    return await view.get_site_stats(request)
