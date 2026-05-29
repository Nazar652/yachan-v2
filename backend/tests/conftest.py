import os
from collections.abc import Callable
from unittest.mock import AsyncMock, MagicMock

import pytest

# required settings must exist before importing anything that builds Settings at
# import time; setdefault keeps real env values when they are present
os.environ.setdefault("JWT_SECRET", "test-jwt-secret-change-me-in-tests")
os.environ.setdefault("IP_HASH_SALT", "test-salt")


@pytest.fixture
def session() -> MagicMock:
    """A mock AsyncSession: async io methods are awaitable, add/add_all are sync."""
    mock_session = MagicMock()
    mock_session.execute = AsyncMock()
    mock_session.flush = AsyncMock()
    mock_session.refresh = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_session.close = AsyncMock()
    return mock_session


@pytest.fixture
def make_result() -> Callable[..., MagicMock]:
    """Factory for a mock result returned by session.execute(...)."""

    def _make(
        *,
        one_or_none: object = None,
        one: object = None,
        all_: list | None = None,
        first: object = None,
        rowcount: int = 0,
    ) -> MagicMock:
        result = MagicMock()
        result.scalar_one_or_none.return_value = one_or_none
        result.scalar_one.return_value = one
        scalars = MagicMock()
        scalars.all.return_value = all_ if all_ is not None else []
        scalars.first.return_value = first
        result.scalars.return_value = scalars
        result.rowcount = rowcount
        return result

    return _make
