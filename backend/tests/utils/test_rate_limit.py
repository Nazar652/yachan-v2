from unittest.mock import AsyncMock, MagicMock

from src.utils.rate_limit import RateLimiter


def _make_limiter(count: int) -> tuple[RateLimiter, AsyncMock]:
    script = AsyncMock(return_value=count)
    redis_client = MagicMock()
    redis_client.register_script = MagicMock(return_value=script)
    return RateLimiter(redis_client), script


async def test_within_limit_allowed_and_runs_atomic_script():
    limiter, script = _make_limiter(3)

    assert await limiter.is_allowed("k", limit=5, window_seconds=60) is True
    script.assert_awaited_once_with(keys=["k"], args=[60])


async def test_first_hit_allowed():
    limiter, _ = _make_limiter(1)

    assert await limiter.is_allowed("k", limit=5, window_seconds=60) is True


async def test_over_limit_disallowed():
    limiter, _ = _make_limiter(6)

    assert await limiter.is_allowed("k", limit=5, window_seconds=60) is False
