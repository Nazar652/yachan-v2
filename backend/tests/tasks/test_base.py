from unittest.mock import AsyncMock, MagicMock

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


def test_commits_and_closes_on_success():
    session = MagicMock()
    session.commit = AsyncMock()
    session.close = AsyncMock()

    _commit_task(session)

    session.commit.assert_awaited_once()
    session.close.assert_awaited_once()
    assert current_scope() is None


def test_rolls_back_and_reraises_on_error():
    session = MagicMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()

    with pytest.raises(ValueError, match="boom"):
        _failing_task(session)

    session.rollback.assert_awaited_once()
    session.close.assert_awaited_once()
    assert current_scope() is None


def test_no_session_is_fine():
    assert _no_session_task() == "done"
    assert current_scope() is None
