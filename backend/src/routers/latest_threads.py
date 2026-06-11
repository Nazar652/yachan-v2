from fastapi import APIRouter, Depends

from src.bootstrap.container import get_dependency
from src.schemas.thread import LatestThreadResponse
from src.views.threads_view import ThreadsView

router = APIRouter(prefix="/threads", tags=["threads"])


@router.get("/latest", response_model=list[LatestThreadResponse])
async def list_latest_threads(
    limit: int = 5, view: ThreadsView = Depends(lambda: get_dependency(ThreadsView))
) -> list[LatestThreadResponse]:
    return await view.list_latest_threads(limit)
