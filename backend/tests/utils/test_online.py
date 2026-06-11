from unittest.mock import AsyncMock, MagicMock

from src.utils.online import ONLINE_WINDOW_SECONDS, OnlineTracker, board_online_key


def _make_redis(execute_results: list | None = None) -> MagicMock:
    redis_client = MagicMock()
    pipeline = MagicMock()
    pipeline.execute = AsyncMock(return_value=execute_results or [])
    redis_client.pipeline.return_value = pipeline
    return redis_client


def test_board_online_key():
    assert board_online_key("b") == "online:board:b"


async def test_touch_records_site_presence():
    redis_client = _make_redis()
    pipeline = redis_client.pipeline.return_value
    tracker = OnlineTracker(redis_client)

    await tracker.touch("hash")

    pipeline.zadd.assert_called_once()
    assert pipeline.zadd.call_args.args[0] == "online:site"
    pipeline.expire.assert_called_once_with("online:site", ONLINE_WINDOW_SECONDS)
    pipeline.execute.assert_awaited_once()


async def test_touch_with_board_records_site_and_board():
    redis_client = _make_redis()
    pipeline = redis_client.pipeline.return_value
    tracker = OnlineTracker(redis_client)

    await tracker.touch("hash", "b")

    zadd_keys = [call.args[0] for call in pipeline.zadd.call_args_list]
    assert zadd_keys == ["online:site", "online:board:b"]
    pipeline.execute.assert_awaited_once()


async def test_count_site_prunes_then_counts():
    redis_client = _make_redis([0, 3])
    pipeline = redis_client.pipeline.return_value
    tracker = OnlineTracker(redis_client)

    assert await tracker.count_site() == 3
    pipeline.zremrangebyscore.assert_called_once()
    assert pipeline.zremrangebyscore.call_args.args[0] == "online:site"
    pipeline.zcard.assert_called_once_with("online:site")


async def test_count_by_board_maps_counts_to_slugs():
    redis_client = _make_redis([0, 2, 0, 5])
    tracker = OnlineTracker(redis_client)

    assert await tracker.count_by_board(["a", "b"]) == {"a": 2, "b": 5}


async def test_count_by_board_empty_skips_redis():
    redis_client = _make_redis()
    tracker = OnlineTracker(redis_client)

    assert await tracker.count_by_board([]) == {}
    redis_client.pipeline.assert_not_called()
