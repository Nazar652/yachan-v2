from unittest.mock import AsyncMock, MagicMock

from src.core.rate_limit import RateLimiter


def _make_redis(count: int) -> MagicMock:
    redis_client = MagicMock()
    redis_client.incr = AsyncMock(return_value=count)
    redis_client.expire = AsyncMock()
    return redis_client


async def test_first_hit_allowed_and_sets_expiry():
    redis_client = _make_redis(1)
    limiter = RateLimiter(redis_client)

    assert await limiter.is_allowed("k", limit=5, window_seconds=60) is True
    redis_client.expire.assert_awaited_once_with("k", 60)


async def test_subsequent_hit_within_limit_does_not_reset_expiry():
    redis_client = _make_redis(3)
    limiter = RateLimiter(redis_client)

    assert await limiter.is_allowed("k", limit=5, window_seconds=60) is True
    redis_client.expire.assert_not_called()


async def test_over_limit_disallowed():
    redis_client = _make_redis(6)
    limiter = RateLimiter(redis_client)

    assert await limiter.is_allowed("k", limit=5, window_seconds=60) is False
    redis_client.expire.assert_not_called()
