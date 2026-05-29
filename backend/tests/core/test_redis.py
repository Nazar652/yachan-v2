from redis.asyncio import Redis
from src.core.redis import get_redis


def test_get_redis_returns_client_and_is_cached():
    client = get_redis()
    assert isinstance(client, Redis)
    assert get_redis() is client
