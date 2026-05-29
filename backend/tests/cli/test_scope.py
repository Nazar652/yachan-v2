from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from src.bootstrap.scope import close_scope, current_scope
from src.cli.scope import run_in_scope


@pytest.fixture(autouse=True)
def _clean_scope():
    close_scope()
    yield
    close_scope()


async def test_commits_and_closes_on_success():
    session = MagicMock()
    session.commit = AsyncMock()
    session.close = AsyncMock()

    async def work():
        current_scope()[AsyncSession] = session
        return "result"

    assert await run_in_scope(work) == "result"
    session.commit.assert_awaited_once()
    session.close.assert_awaited_once()
    assert current_scope() is None


async def test_rolls_back_and_reraises_on_error():
    session = MagicMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()

    async def work():
        current_scope()[AsyncSession] = session
        raise ValueError("boom")

    with pytest.raises(ValueError, match="boom"):
        await run_in_scope(work)
    session.rollback.assert_awaited_once()
    session.close.assert_awaited_once()
    assert current_scope() is None
