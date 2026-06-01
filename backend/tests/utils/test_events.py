import json
from unittest.mock import AsyncMock, MagicMock

from src.utils.events import NEW_POST, EventPublisher, board_channel, thread_channel


def test_thread_channel():
    assert thread_channel(5) == "ws:thread:5"


def test_board_channel():
    assert board_channel("b") == "ws:board:b"


async def test_publish_serializes_envelope():
    redis = MagicMock()
    redis.publish = AsyncMock()
    publisher = EventPublisher(redis)

    await publisher.publish("ws:thread:5", NEW_POST, {"post_number": 1})

    redis.publish.assert_awaited_once()
    channel, payload = redis.publish.await_args.args
    assert channel == "ws:thread:5"
    assert json.loads(payload) == {"type": "new_post", "data": {"post_number": 1}}
