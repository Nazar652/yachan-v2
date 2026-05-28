from unittest.mock import AsyncMock, MagicMock

from src.schemas.board import BoardResponse
from src.views.boards_view import BoardsView
from tests.views._factories import board_ns


async def test_list_boards_maps_to_responses():
    board_service = MagicMock()
    board_service.list_boards = AsyncMock(return_value=[board_ns(), board_ns(id=2, slug="g")])
    view = BoardsView(board_service=board_service)

    result = await view.list_boards()

    assert all(isinstance(item, BoardResponse) for item in result)
    assert [item.slug for item in result] == ["b", "g"]


async def test_get_board_maps_to_response():
    board_service = MagicMock()
    board_service.get_board = AsyncMock(return_value=board_ns())
    view = BoardsView(board_service=board_service)

    result = await view.get_board("b")

    assert isinstance(result, BoardResponse)
    board_service.get_board.assert_awaited_once_with("b")
