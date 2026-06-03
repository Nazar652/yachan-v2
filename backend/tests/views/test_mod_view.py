from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from src.core.exceptions import ForbiddenError
from src.models.mod_account import ModRole
from src.schemas.board import BoardCreate, BoardReorder, BoardResponse, BoardUpdate
from src.schemas.mod import BanCreate, BanResponse, ModLogin, TokenResponse
from src.views.mod_view import ModView
from tests.views._factories import ban_ns, board_ns


def build(*, role=ModRole.ADMIN):
    mod = SimpleNamespace(id=99, role=role)
    mod_service = MagicMock()
    mod_service.authenticate = AsyncMock(return_value=("jwt-token", role))
    mod_service.resolve_mod = AsyncMock(return_value=mod)
    mod_service.delete_post = AsyncMock()
    mod_service.set_thread_locked = AsyncMock()
    mod_service.ban_poster = AsyncMock(return_value=ban_ns())
    board_service = MagicMock()
    board_service.create_board = AsyncMock(return_value=board_ns())
    board_service.update_board = AsyncMock(return_value=board_ns())
    board_service.reorder_boards = AsyncMock(return_value=[board_ns()])
    report_service = MagicMock()
    report_service.list_unresolved = AsyncMock(return_value=[])
    report_service.resolve = AsyncMock()
    view = ModView(
        mod_service=mod_service,
        board_service=board_service,
        report_service=report_service,
    )
    return view, SimpleNamespace(
        mod_service=mod_service, board_service=board_service, report_service=report_service
    )


async def test_login_returns_token_and_role():
    view, _ = build(role=ModRole.ADMIN)
    result = await view.login(ModLogin(username="admin", password="pw"))
    assert isinstance(result, TokenResponse)
    assert result.access_token == "jwt-token"
    assert result.role is ModRole.ADMIN


async def test_create_board_admin_only_ok():
    view, mocks = build(role=ModRole.ADMIN)
    result = await view.create_board("tok", BoardCreate(slug="b", title="x"))
    assert isinstance(result, BoardResponse)
    mocks.board_service.create_board.assert_awaited_once()


async def test_create_board_rejects_non_admin():
    view, mocks = build(role=ModRole.MODERATOR)
    with pytest.raises(ForbiddenError):
        await view.create_board("tok", BoardCreate(slug="b", title="x"))
    mocks.board_service.create_board.assert_not_called()


async def test_update_board_admin_only_ok():
    view, mocks = build(role=ModRole.ADMIN)
    result = await view.update_board("tok", "b", BoardUpdate(title="new"))
    assert isinstance(result, BoardResponse)
    mocks.board_service.update_board.assert_awaited_once()


async def test_update_board_rejects_non_admin():
    view, mocks = build(role=ModRole.MODERATOR)
    with pytest.raises(ForbiddenError):
        await view.update_board("tok", "b", BoardUpdate(title="new"))
    mocks.board_service.update_board.assert_not_called()


async def test_reorder_boards_admin_only_ok():
    view, mocks = build(role=ModRole.ADMIN)
    result = await view.reorder_boards("tok", BoardReorder(slugs=["g", "b"]))
    assert isinstance(result, list)
    assert all(isinstance(item, BoardResponse) for item in result)
    mocks.board_service.reorder_boards.assert_awaited_once_with(["g", "b"])


async def test_reorder_boards_rejects_non_admin():
    view, mocks = build(role=ModRole.MODERATOR)
    with pytest.raises(ForbiddenError):
        await view.reorder_boards("tok", BoardReorder(slugs=["g", "b"]))
    mocks.board_service.reorder_boards.assert_not_called()


async def test_delete_post_delegates_with_mod():
    view, mocks = build()
    await view.delete_post("tok", "b", 5)
    mocks.mod_service.delete_post.assert_awaited_once()


async def test_ban_poster_returns_response():
    view, _ = build()
    result = await view.ban_poster("tok", "b", 5, BanCreate(reason="spam"))
    assert isinstance(result, BanResponse)


async def test_resolve_report_uses_mod_id():
    view, mocks = build()
    await view.resolve_report("tok", 7)
    mocks.report_service.resolve.assert_awaited_once_with(7, 99)
