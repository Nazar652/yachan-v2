from fastapi import APIRouter, Depends

from src.schemas.board import BoardResponse
from src.views.boards_view import BoardsView

router = APIRouter(prefix="/boards", tags=["boards"])


def _view() -> BoardsView:
    return BoardsView()


@router.get("", response_model=list[BoardResponse])
async def list_boards(view: BoardsView = Depends(_view)) -> list[BoardResponse]:
    return await view.list_boards()


@router.get("/{slug}", response_model=BoardResponse)
async def get_board(slug: str, view: BoardsView = Depends(_view)) -> BoardResponse:
    return await view.get_board(slug)
