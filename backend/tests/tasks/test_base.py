from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from src.bootstrap.scope import current_scope
from src.celery_app import celery
from src.tasks.base import ScopedTask


@celery.task(base=ScopedTask, name="_test_commit_task")
async def _commit_task(session):
    current_scope()[AsyncSession] = session


@celery.task(base=ScopedTask, name="_test_failing_task")
async def _failing_task(session):
    current_scope()[AsyncSession] = session
    raise ValueError("boom")


@celery.task(base=ScopedTask, name="_test_no_session_task")
async def _no_session_task():
    return "done"


@patch("src.tasks.base.get_engine")
def test_commits_and_closes_on_success(get_engine):
    get_engine.return_value.dispose = AsyncMock()
    session = MagicMock()
    session.commit = AsyncMock()
    session.close = AsyncMock()

    _commit_task(session)

    session.commit.assert_awaited_once()
    session.close.assert_awaited_once()
    get_engine.return_value.dispose.assert_awaited_once()
    assert current_scope() is None


@patch("src.tasks.base.get_engine")
def test_rolls_back_and_reraises_on_error(get_engine):
    get_engine.return_value.dispose = AsyncMock()
    session = MagicMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()

    with pytest.raises(ValueError, match="boom"):
        _failing_task(session)

    session.rollback.assert_awaited_once()
    session.close.assert_awaited_once()
    get_engine.return_value.dispose.assert_awaited_once()
    assert current_scope() is None


@patch("src.tasks.base.get_engine")
def test_no_session_skips_engine_dispose(get_engine):
    assert _no_session_task() == "done"
    get_engine.assert_not_called()
    assert current_scope() is None
