from fastapi import APIRouter, Depends, Request

from src.bootstrap.container import get_dependency
from src.schemas.board import BoardResponse
from src.views.boards_view import BoardsView

router = APIRouter(prefix="/boards", tags=["boards"])


@router.get("", response_model=list[BoardResponse])
async def list_boards(
    request: Request, view: BoardsView = Depends(lambda: get_dependency(BoardsView))
) -> list[BoardResponse]:
    return await view.list_boards(request)


@router.get("/{slug}", response_model=BoardResponse)
async def get_board(slug: str, view: BoardsView = Depends(lambda: get_dependency(BoardsView))) -> BoardResponse:
    return await view.get_board(slug)
