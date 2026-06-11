from unittest.mock import AsyncMock, MagicMock

from src.schemas.board import BoardResponse
from src.views.boards_view import BoardsView
from tests.views._factories import board_ns, request_ns, settings_ns


def build(boards=None):
    board_service = MagicMock()
    board_service.list_boards = AsyncMock(return_value=boards or [board_ns()])
    board_service.get_board = AsyncMock(return_value=board_ns())
    online_tracker = MagicMock()
    online_tracker.touch = AsyncMock()
    view = BoardsView(
        board_service=board_service,
        online_tracker=online_tracker,
        settings=settings_ns(),
    )
    return view, board_service, online_tracker


async def test_list_boards_maps_to_responses():
    view, board_service, online_tracker = build(boards=[board_ns(), board_ns(id=2, slug="g")])

    result = await view.list_boards(request_ns())

    assert all(isinstance(item, BoardResponse) for item in result)
    assert [item.slug for item in result] == ["b", "g"]


async def test_list_boards_touches_site_presence():
    view, board_service, online_tracker = build()

    await view.list_boards(request_ns())

    online_tracker.touch.assert_awaited_once()


async def test_get_board_maps_to_response():
    view, board_service, online_tracker = build()

    result = await view.get_board("b")

    assert isinstance(result, BoardResponse)
    board_service.get_board.assert_awaited_once_with("b")
