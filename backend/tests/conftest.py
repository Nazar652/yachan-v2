from collections.abc import Callable
from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.fixture
def session() -> MagicMock:
    """A mock AsyncSession: async io methods are awaitable, add/add_all are sync."""
    s = MagicMock()
    s.execute = AsyncMock()
    s.flush = AsyncMock()
    s.refresh = AsyncMock()
    s.commit = AsyncMock()
    s.rollback = AsyncMock()
    s.close = AsyncMock()
    return s


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
