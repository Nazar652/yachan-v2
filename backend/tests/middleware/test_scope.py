from unittest.mock import AsyncMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.bootstrap.scope import close_scope, current_scope
from src.middleware.scope import ScopeMiddleware


@pytest.fixture(autouse=True)
def _clean_scope():
    close_scope()
    yield
    close_scope()


async def test_non_http_passes_through(session):
    app = AsyncMock()
    mw = ScopeMiddleware(app)
    recv, send = AsyncMock(), AsyncMock()

    await mw({"type": "lifespan"}, recv, send)

    app.assert_awaited_once_with({"type": "lifespan"}, recv, send)
    session.commit.assert_not_called()


async def test_http_success_commits_and_closes(session):
    async def app(scope, receive, send):
        current_scope()[AsyncSession] = session

    mw = ScopeMiddleware(app)
    await mw({"type": "http"}, AsyncMock(), AsyncMock())

    session.commit.assert_awaited_once()
    session.rollback.assert_not_called()
    session.close.assert_awaited_once()
    assert current_scope() is None


async def test_http_exception_rolls_back_and_reraises(session):
    async def app(scope, receive, send):
        current_scope()[AsyncSession] = session
        raise ValueError("boom")

    mw = ScopeMiddleware(app)
    with pytest.raises(ValueError, match="boom"):
        await mw({"type": "http"}, AsyncMock(), AsyncMock())

    session.rollback.assert_awaited_once()
    session.commit.assert_not_called()
    session.close.assert_awaited_once()
    assert current_scope() is None


async def test_http_without_session_in_scope_does_not_touch_db(session):
    async def app(scope, receive, send):
        pass  # no session created during the request

    mw = ScopeMiddleware(app)
    await mw({"type": "http"}, AsyncMock(), AsyncMock())

    session.commit.assert_not_called()
    session.close.assert_not_called()
