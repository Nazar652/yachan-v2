from redis.asyncio import Redis

# incr + first-hit expire in one atomic step. done as two commands, a crash between
# them would leave the key without a ttl and block it forever; tying expire to the
# first hit keeps fixed-window semantics (no sliding refresh on every request).
_INCREMENT_WITH_EXPIRY = """
local count = redis.call('INCR', KEYS[1])
if count == 1 then
    redis.call('EXPIRE', KEYS[1], ARGV[1])
end
return count
"""


class RateLimiter:
    """Fixed-window limiter backed by redis."""

    def __init__(self, redis: Redis) -> None:
        self.redis = redis
        self.increment_with_expiry = redis.register_script(_INCREMENT_WITH_EXPIRY)

    async def is_allowed(self, key: str, limit: int, window_seconds: int) -> bool:
        count = await self.increment_with_expiry(keys=[key], args=[window_seconds])
        return count <= limit
