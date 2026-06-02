from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from src.core.exceptions import BoardAlreadyExistsError, BoardNotFoundError
from src.schemas.board import BoardCreate, BoardUpdate
from src.services.board_service import BoardService


async def test_create_board_creates_row_and_sequence():
    board = SimpleNamespace(id=1, slug="b")
    board_repo = MagicMock()
    board_repo.get_by_slug = AsyncMock(return_value=None)
    board_repo.create = AsyncMock(return_value=board)
    board_repo.create_post_number_sequence = AsyncMock()
    service = BoardService(board_repo=board_repo)

    result = await service.create_board(BoardCreate(slug="b", title="Random"))

    assert result is board
    board_repo.create_post_number_sequence.assert_awaited_once_with("b")


async def test_create_board_rejects_duplicate_slug():
    board_repo = MagicMock()
    board_repo.get_by_slug = AsyncMock(return_value=SimpleNamespace(slug="b"))
    board_repo.create = AsyncMock()
    service = BoardService(board_repo=board_repo)

    with pytest.raises(BoardAlreadyExistsError):
        await service.create_board(BoardCreate(slug="b", title="x"))
    board_repo.create.assert_not_called()


async def test_get_board_raises_when_missing():
    board_repo = MagicMock()
    board_repo.get_by_slug = AsyncMock(return_value=None)
    service = BoardService(board_repo=board_repo)

    with pytest.raises(BoardNotFoundError):
        await service.get_board("nope")


async def test_update_board_applies_only_set_fields():
    board = SimpleNamespace(
        slug="b", title="old", description="old desc", bump_limit=300, is_active=True
    )
    board_repo = MagicMock()
    board_repo.get_by_slug = AsyncMock(return_value=board)
    board_repo.update = AsyncMock(side_effect=lambda updated: updated)
    service = BoardService(board_repo=board_repo)

    result = await service.update_board("b", BoardUpdate(title="new", is_active=False))

    assert result.title == "new"
    assert result.is_active is False
    assert result.description == "old desc"  # not in the payload, left untouched
    board_repo.update.assert_awaited_once_with(board)


async def test_update_board_raises_when_missing():
    board_repo = MagicMock()
    board_repo.get_by_slug = AsyncMock(return_value=None)
    board_repo.update = AsyncMock()
    service = BoardService(board_repo=board_repo)

    with pytest.raises(BoardNotFoundError):
        await service.update_board("nope", BoardUpdate(title="x"))
    board_repo.update.assert_not_called()


async def test_list_boards_delegates():
    boards = [object()]
    board_repo = MagicMock()
    board_repo.list_all = AsyncMock(return_value=boards)
    service = BoardService(board_repo=board_repo)

    assert await service.list_boards() == boards
