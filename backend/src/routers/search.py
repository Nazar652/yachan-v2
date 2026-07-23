from fastapi import APIRouter, Depends, Query, Request

from src.bootstrap.container import get_dependency
from src.schemas.search import SearchResultResponse
from src.views.search_view import SearchView

router = APIRouter(prefix="/search", tags=["search"])


@router.get("", response_model=list[SearchResultResponse])
async def search(
    request: Request,
    q: str = Query(min_length=1, max_length=200),
    board: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=50),
    view: SearchView = Depends(lambda: get_dependency(SearchView)),
) -> list[SearchResultResponse]:
    return await view.search(q, board, limit, request)
