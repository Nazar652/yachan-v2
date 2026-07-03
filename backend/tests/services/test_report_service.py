from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from src.core.exceptions import BoardNotFoundError, PostNotFoundError
from src.schemas.report import ReportCreate
from src.services.report_service import ReportService


def build(*, board=SimpleNamespace(id=1), post=SimpleNamespace(id=10, board_id=1)):
    board_repo = MagicMock()
    board_repo.get_by_slug = AsyncMock(return_value=board)
    post_repo = MagicMock()
    post_repo.get_by_board_and_number = AsyncMock(return_value=post)
    post_repo.get_by_id = AsyncMock(return_value=post)
    report_repo = MagicMock()
    report_repo.create = AsyncMock(return_value=SimpleNamespace(id=1))
    report_repo.list_unresolved = AsyncMock(return_value=[])
    report_repo.mark_resolved = AsyncMock()
    report_repo.count_auto_for_post = AsyncMock(return_value=0)
    service = ReportService(
        report_repo=report_repo, post_repo=post_repo, board_repo=board_repo
    )
    return service, SimpleNamespace(report_repo=report_repo, post_repo=post_repo)


async def test_create_report_happy_path():
    service, mocks = build()
    await service.create_report("b", 10, ReportCreate(reason="spam"), "iphash")
    mocks.report_repo.create.assert_awaited_once()


async def test_create_report_unknown_board():
    service, _ = build(board=None)
    with pytest.raises(BoardNotFoundError):
        await service.create_report("b", 10, ReportCreate(), "iphash")


async def test_create_report_unknown_post():
    service, _ = build(post=None)
    with pytest.raises(PostNotFoundError):
        await service.create_report("b", 10, ReportCreate(), "iphash")


async def test_resolve_delegates():
    service, mocks = build()
    await service.resolve(7, mod_id=2)
    mocks.report_repo.mark_resolved.assert_awaited_once_with(7, 2)


async def test_apply_text_verdict_creates_auto_report_for_toxic():
    service, mocks = build()
    await service.apply_text_verdict(10, {"toxic": True, "spam": False})
    mocks.report_repo.create.assert_awaited_once()
    created = mocks.report_repo.create.await_args.args[0]
    assert created.is_auto is True
    assert created.board_id == 1
    assert "toxicity" in created.reason
    assert "spam" not in created.reason


async def test_apply_text_verdict_lists_both_labels():
    service, mocks = build()
    await service.apply_text_verdict(10, {"toxic": True, "spam": True})
    created = mocks.report_repo.create.await_args.args[0]
    assert "toxicity" in created.reason
    assert "spam" in created.reason


async def test_apply_text_verdict_clean_post_does_nothing():
    service, mocks = build()
    assert await service.apply_text_verdict(10, {"toxic": False, "spam": False}) is None
    mocks.report_repo.create.assert_not_awaited()


async def test_create_auto_report_skips_when_already_auto_reported():
    service, mocks = build()
    mocks.report_repo.count_auto_for_post = AsyncMock(return_value=1)
    assert await service.create_auto_report(10, "Auto-flagged: spam") is None
    mocks.report_repo.create.assert_not_awaited()


async def test_create_auto_report_skips_missing_post():
    service, mocks = build()
    mocks.post_repo.get_by_id = AsyncMock(return_value=None)
    assert await service.create_auto_report(10, "Auto-flagged: spam") is None
    mocks.report_repo.create.assert_not_awaited()
