from redis.asyncio import Redis

from src.utils.clock import utcnow

ONLINE_WINDOW_SECONDS = 300

_SITE_KEY = "online:site"


def board_online_key(board_slug: str) -> str:
    return f"online:board:{board_slug}"


class OnlineTracker:
    """Sliding-window unique-visitor presence backed by redis sorted sets.

    Pipeline commands only queue and return the pipeline itself, so they are
    deliberately not awaited — the single await is execute().
    """

    def __init__(self, redis: Redis, window_seconds: int = ONLINE_WINDOW_SECONDS) -> None:
        self.redis = redis
        self.window_seconds = window_seconds

    # noinspection PyAsyncCall
    async def touch(self, ip_hash: str, board_slug: str | None = None) -> None:
        now = utcnow().timestamp()
        pipeline = self.redis.pipeline()
        pipeline.zadd(_SITE_KEY, {ip_hash: now})
        pipeline.expire(_SITE_KEY, self.window_seconds)
        if board_slug is not None:
            board_key = board_online_key(board_slug)
            pipeline.zadd(board_key, {ip_hash: now})
            pipeline.expire(board_key, self.window_seconds)
        await pipeline.execute()

    async def count_site(self) -> int:
        counts = await self._count(_SITE_KEY)
        return counts[0]

    async def count_by_board(self, board_slugs: list[str]) -> dict[str, int]:
        if not board_slugs:
            return {}
        counts = await self._count(*[board_online_key(slug) for slug in board_slugs])
        return dict(zip(board_slugs, counts, strict=True))

    # noinspection PyAsyncCall
    async def _count(self, *keys: str) -> list[int]:
        # prune entries older than the window, then count what is left
        cutoff = utcnow().timestamp() - self.window_seconds
        pipeline = self.redis.pipeline()
        for key in keys:
            pipeline.zremrangebyscore(key, "-inf", cutoff)
            pipeline.zcard(key)
        results = await pipeline.execute()
        return [int(count) for count in results[1::2]]
