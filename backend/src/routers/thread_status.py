from typing import Annotated

from fastapi import APIRouter, Depends, Query

from src.bootstrap.container import get_dependency
from src.schemas.thread import ThreadStatusResponse
from src.views.threads_view import ThreadsView

router = APIRouter(prefix="/threads", tags=["threads"])


@router.get("/status", response_model=list[ThreadStatusResponse])
async def get_thread_statuses(
    ids: Annotated[list[int], Query()],
    view: ThreadsView = Depends(lambda: get_dependency(ThreadsView)),
) -> list[ThreadStatusResponse]:
    return await view.get_thread_statuses(ids)
