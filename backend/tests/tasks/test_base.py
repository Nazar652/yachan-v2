import json
import logging
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from src.bootstrap.scope import current_scope
from src.celery_app import celery
from src.tasks.base import ScopedTask
from src.utils.request_context import get_request_id


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


@celery.task(base=ScopedTask, name="_test_captures_request_id_task")
async def _captures_request_id_task(captured):
    captured["request_id"] = get_request_id()


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


def test_logs_task_invoked_on_success(caplog):
    with patch("src.tasks.base.get_engine") as get_engine:
        get_engine.return_value.dispose = AsyncMock()
        session = MagicMock()
        session.commit = AsyncMock()
        session.close = AsyncMock()

        with caplog.at_level(logging.INFO, logger="src.tasks"):
            _commit_task(session)

    payload = json.loads(caplog.records[-1].message)
    assert payload["event"] == "task_invoked"
    assert payload["task_name"] == "_test_commit_task"
    assert payload["status"] == "success"
    assert payload["error"] is None
    assert isinstance(payload["duration_ms"], float)


def test_logs_task_invoked_on_failure(caplog):
    with patch("src.tasks.base.get_engine") as get_engine:
        get_engine.return_value.dispose = AsyncMock()
        session = MagicMock()
        session.rollback = AsyncMock()
        session.close = AsyncMock()

        with caplog.at_level(logging.INFO, logger="src.tasks"), pytest.raises(ValueError):
            _failing_task(session)

    payload = json.loads(caplog.records[-1].message)
    assert payload["status"] == "failure"
    assert payload["error"] == "boom"


def test_propagates_request_id_from_message_headers():
    with patch("src.tasks.base.get_engine"):
        captured: dict = {}
        _captures_request_id_task.push_request(headers={"request_id": "req-99"})
        try:
            _captures_request_id_task(captured)
        finally:
            _captures_request_id_task.pop_request()

    assert captured["request_id"] == "req-99"
    assert get_request_id() is None


def test_request_id_is_none_without_message_headers():
    captured: dict = {}
    _captures_request_id_task(captured)
    assert captured["request_id"] is None
