from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.core.exceptions import BoardNotFoundError, PostNotFoundError
from src.schemas.report import ReportCreate
from src.services.report_service import ReportService


def build(*, board=SimpleNamespace(id=1), post=SimpleNamespace(id=10)):
    board_repo = MagicMock()
    board_repo.get_by_slug = AsyncMock(return_value=board)
    post_repo = MagicMock()
    post_repo.get_by_board_and_number = AsyncMock(return_value=post)
    report_repo = MagicMock()
    report_repo.create = AsyncMock(return_value=SimpleNamespace(id=1))
    report_repo.list_unresolved = AsyncMock(return_value=[])
    report_repo.mark_resolved = AsyncMock()
    service = ReportService(
        report_repo=report_repo, post_repo=post_repo, board_repo=board_repo
    )
    return service, SimpleNamespace(report_repo=report_repo)


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
