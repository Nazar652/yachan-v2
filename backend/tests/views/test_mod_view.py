from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from src.core.exceptions import ForbiddenError, SummaryNotConfiguredError, ThreadTooShortForSummaryError
from src.models.mod_account import ModRole
from src.schemas.board import BoardCreate, BoardReorder, BoardResponse, BoardUpdate
from src.schemas.mod import BanCreate, BanResponse, ModLogin, TokenResponse
from src.schemas.report import ReportResponse
from src.views.mod_view import ModView
from tests.views._factories import ban_ns, board_ns, post_ns, report_ns, thread_ns


def build(*, role=ModRole.ADMIN, gemini_api_key="key", posts=None):
    mod = SimpleNamespace(id=99, role=role)
    mod_service = MagicMock()
    mod_service.authenticate = AsyncMock(return_value=("jwt-token", role))
    mod_service.resolve_mod = AsyncMock(return_value=mod)
    mod_service.delete_post = AsyncMock()
    mod_service.set_thread_locked = AsyncMock(return_value=thread_ns(is_locked=True))
    mod_service.set_thread_sticky = AsyncMock(return_value=thread_ns(is_sticky=True))
    mod_service.ban_poster = AsyncMock(return_value=ban_ns())
    board_service = MagicMock()
    board_service.create_board = AsyncMock(return_value=board_ns())
    board_service.update_board = AsyncMock(return_value=board_ns())
    board_service.reorder_boards = AsyncMock(return_value=[board_ns()])
    report_service = MagicMock()
    report_service.list_unresolved = AsyncMock(return_value=[])
    report_service.resolve = AsyncMock()
    thread_service = MagicMock()
    thread_service.delete_thread = AsyncMock(return_value=thread_ns(id=5))
    thread_service.get_thread_detail = AsyncMock(
        return_value=(
            thread_ns(id=5),
            posts if posts is not None else [post_ns(id=i, post_number=i) for i in range(1, 15)],
            {},
        )
    )
    summary_service = MagicMock()
    summary_service.summarize_thread = AsyncMock()
    events = MagicMock()
    events.publish = AsyncMock()
    settings = SimpleNamespace(gemini_api_key=gemini_api_key)
    view = ModView(
        mod_service=mod_service,
        board_service=board_service,
        report_service=report_service,
        thread_service=thread_service,
        summary_service=summary_service,
        events=events,
        settings=settings,
    )
    return view, SimpleNamespace(
        mod_service=mod_service,
        board_service=board_service,
        report_service=report_service,
        thread_service=thread_service,
        summary_service=summary_service,
        events=events,
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


async def test_delete_thread_admin_publishes_to_both_channels():
    view, mocks = build(role=ModRole.ADMIN)

    await view.delete_thread("tok", "b", 5)

    mocks.thread_service.delete_thread.assert_awaited_once_with("b", 5)
    channels = [call.args[0] for call in mocks.events.publish.await_args_list]
    assert channels == ["ws:thread:5", "ws:board:b"]
    for call in mocks.events.publish.await_args_list:
        assert call.args[1] == "thread_deleted"
        assert call.args[2] == {"id": 5}


async def test_delete_thread_rejects_non_admin():
    view, mocks = build(role=ModRole.MODERATOR)
    with pytest.raises(ForbiddenError):
        await view.delete_thread("tok", "b", 5)
    mocks.thread_service.delete_thread.assert_not_called()
    mocks.events.publish.assert_not_called()


async def test_ban_poster_returns_response():
    view, _ = build()
    result = await view.ban_poster("tok", "b", 5, BanCreate(reason="spam"))
    assert isinstance(result, BanResponse)


async def test_list_reports_maps_post_and_board_location():
    view, mocks = build()
    mocks.report_service.list_unresolved = AsyncMock(
        return_value=[(report_ns(), 3, 5, "b")]
    )

    result = await view.list_reports("tok")

    assert len(result) == 1
    assert isinstance(result[0], ReportResponse)
    assert result[0].board_slug == "b"
    assert result[0].thread_id == 5
    assert result[0].post_number == 3


async def test_resolve_report_uses_mod_id():
    view, mocks = build()
    await view.resolve_report("tok", 7)
    mocks.report_service.resolve.assert_awaited_once_with(7, 99)


async def test_set_thread_locked_publishes_to_both_channels():
    view, mocks = build()
    await view.set_thread_locked("tok", "b", 5, True)

    mocks.mod_service.set_thread_locked.assert_awaited_once_with("b", 5, True)
    channels = [call.args[0] for call in mocks.events.publish.await_args_list]
    assert channels == ["ws:thread:5", "ws:board:b"]
    for call in mocks.events.publish.await_args_list:
        assert call.args[1] == "thread_updated"
        assert call.args[2]["id"] == 5
        assert call.args[2]["is_locked"] is True


async def test_set_thread_sticky_publishes_to_both_channels():
    view, mocks = build()
    await view.set_thread_sticky("tok", "b", 5, True)

    mocks.mod_service.set_thread_sticky.assert_awaited_once_with("b", 5, True)
    channels = [call.args[0] for call in mocks.events.publish.await_args_list]
    assert channels == ["ws:thread:5", "ws:board:b"]
    for call in mocks.events.publish.await_args_list:
        assert call.args[1] == "thread_updated"
        assert call.args[2]["is_sticky"] is True


async def test_regenerate_summary_delegates_to_service():
    view, mocks = build(role=ModRole.ADMIN)
    await view.regenerate_summary("tok", "b", 5)
    mocks.summary_service.summarize_thread.assert_awaited_once_with(5)


async def test_regenerate_summary_rejects_non_admin():
    view, mocks = build(role=ModRole.MODERATOR)
    with pytest.raises(ForbiddenError):
        await view.regenerate_summary("tok", "b", 5)
    mocks.summary_service.summarize_thread.assert_not_called()


async def test_regenerate_summary_rejects_when_not_configured():
    view, mocks = build(gemini_api_key="")
    with pytest.raises(SummaryNotConfiguredError):
        await view.regenerate_summary("tok", "b", 5)
    mocks.summary_service.summarize_thread.assert_not_called()


async def test_regenerate_summary_rejects_thread_below_threshold():
    view, mocks = build(posts=[post_ns(id=1, post_number=1)])
    with pytest.raises(ThreadTooShortForSummaryError):
        await view.regenerate_summary("tok", "b", 5)
    mocks.summary_service.summarize_thread.assert_not_called()
