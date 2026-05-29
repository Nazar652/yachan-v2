from redis.asyncio import Redis


class RateLimiter:
    """Fixed-window limiter backed by redis."""

    def __init__(self, redis: Redis) -> None:
        self.redis = redis

    async def is_allowed(self, key: str, limit: int, window_seconds: int) -> bool:
        count = await self.redis.incr(key)
        if count == 1:
            # first hit in this window starts the expiry countdown
            await self.redis.expire(key, window_seconds)
        return count <= limit
