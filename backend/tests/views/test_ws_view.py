import json
import logging
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from redis import exceptions as redis_exceptions
from src.views.ws_view import WsView, event_type
from starlette.websockets import WebSocketDisconnect


def test_event_type_parses_type_field():
    assert event_type(json.dumps({"type": "new_post", "data": {}})) == "new_post"


def test_event_type_none_on_invalid_json():
    assert event_type("not json") is None
    assert event_type("42") is None  # valid json, not a dict -> no .get


async def test_forward_sends_only_message_type():
    async def listen():
        yield {"type": "subscribe", "data": 1}
        yield {"type": "message", "data": "payload"}

    pubsub = MagicMock()
    pubsub.listen = listen
    websocket = MagicMock()
    websocket.send_text = AsyncMock()

    await WsView._forward(pubsub, websocket, "conn-1", "ws:thread:5")

    websocket.send_text.assert_awaited_once_with("payload")


async def test_forward_retries_after_timeout():
    # redis pubsub raises redis.exceptions.TimeoutError (not the builtin) on its 5s
    # idle socket_timeout; _forward must swallow that exact class and keep listening.
    call_count = 0

    async def listen():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise redis_exceptions.TimeoutError
        yield {"type": "message", "data": "after-retry"}

    pubsub = MagicMock()
    pubsub.listen = listen
    websocket = MagicMock()
    websocket.send_text = AsyncMock()

    await WsView._forward(pubsub, websocket, "conn-1", "ws:thread:5")

    assert call_count == 2
    websocket.send_text.assert_awaited_once_with("after-retry")


async def test_forward_logs_message_out_with_event_type(caplog):
    async def listen():
        yield {"type": "message", "data": json.dumps({"type": "new_post", "data": {"id": 1}})}

    pubsub = MagicMock()
    pubsub.listen = listen
    websocket = MagicMock()
    websocket.send_text = AsyncMock()

    with caplog.at_level(logging.INFO, logger="src.ws"):
        await WsView._forward(pubsub, websocket, "conn-1", "ws:thread:5")

    payload = json.loads(caplog.records[-1].message)
    assert payload["event"] == "ws_message_out"
    assert payload["connection_id"] == "conn-1"
    assert payload["channel"] == "ws:thread:5"
    assert payload["event_type"] == "new_post"
    assert json.loads(payload["body"])["data"] == {"id": 1}


async def test_pump_propagates_forward_exception():
    async def failing_forward(pubsub, websocket, connection_id, channel):
        raise RuntimeError("forward error")

    async def instant_drain(websocket, connection_id, channel):
        pass

    pubsub = MagicMock()
    websocket = MagicMock()

    with patch.object(WsView, "_forward", failing_forward), patch.object(
        WsView, "_drain", instant_drain
    ):
        with pytest.raises(RuntimeError, match="forward error"):
            await WsView._pump(pubsub, websocket, "conn-1", "ws:thread:5")


async def test_drain_returns_on_disconnect():
    websocket = MagicMock()
    websocket.receive_text = AsyncMock(side_effect=WebSocketDisconnect(code=1000))

    await WsView._drain(websocket, "conn-1", "ws:thread:5")  # returns without raising


async def test_drain_logs_message_in_before_disconnect(caplog):
    websocket = MagicMock()
    websocket.receive_text = AsyncMock(side_effect=["hello", WebSocketDisconnect(code=1000)])

    with caplog.at_level(logging.INFO, logger="src.ws"):
        await WsView._drain(websocket, "conn-1", "ws:thread:5")

    payload = json.loads(caplog.records[-1].message)
    assert payload["event"] == "ws_message_in"
    assert payload["connection_id"] == "conn-1"
    assert payload["body"] == "hello"


async def test_thread_feed_subscribes_accepts_and_cleans_up():
    async def listen():
        if False:  # empty stream so _forward returns immediately
            yield {}

    pubsub = MagicMock()
    pubsub.listen = listen
    pubsub.subscribe = AsyncMock()
    pubsub.unsubscribe = AsyncMock()
    pubsub.aclose = AsyncMock()
    redis = MagicMock()
    redis.pubsub = MagicMock(return_value=pubsub)

    websocket = MagicMock()
    websocket.accept = AsyncMock()
    websocket.send_text = AsyncMock()
    websocket.receive_text = AsyncMock(side_effect=WebSocketDisconnect(code=1000))

    view = WsView(redis=redis)
    await view.thread_feed(websocket, 5)

    websocket.accept.assert_awaited_once()
    pubsub.subscribe.assert_awaited_once_with("ws:thread:5")
    pubsub.unsubscribe.assert_awaited_once_with("ws:thread:5")
    pubsub.aclose.assert_awaited_once()


async def test_feed_logs_connect_and_disconnect_on_clean_close(caplog):
    async def listen():
        if False:
            yield {}

    pubsub = MagicMock()
    pubsub.listen = listen
    pubsub.subscribe = AsyncMock()
    pubsub.unsubscribe = AsyncMock()
    pubsub.aclose = AsyncMock()
    redis = MagicMock()
    redis.pubsub = MagicMock(return_value=pubsub)

    websocket = MagicMock()
    websocket.accept = AsyncMock()
    websocket.send_text = AsyncMock()
    websocket.receive_text = AsyncMock(side_effect=WebSocketDisconnect(code=1000))

    view = WsView(redis=redis)
    with caplog.at_level(logging.INFO, logger="src.ws"):
        await view.board_feed(websocket, "b")

    events = [json.loads(record.message) for record in caplog.records]
    assert events[0]["event"] == "ws_connect"
    assert events[0]["channel"] == "ws:board:b"
    assert events[-1]["event"] == "ws_disconnect"
    assert events[-1]["reason"] == "client_disconnect"
    assert events[-1]["connection_id"] == events[0]["connection_id"]


async def test_feed_logs_disconnect_with_error_reason_and_reraises(caplog):
    pubsub = MagicMock()
    pubsub.subscribe = AsyncMock()
    pubsub.unsubscribe = AsyncMock()
    pubsub.aclose = AsyncMock()
    redis = MagicMock()
    redis.pubsub = MagicMock(return_value=pubsub)

    websocket = MagicMock()
    websocket.accept = AsyncMock()

    view = WsView(redis=redis)
    with patch.object(
        WsView, "_pump", AsyncMock(side_effect=RuntimeError("boom"))
    ), caplog.at_level(logging.INFO, logger="src.ws"):
        with pytest.raises(RuntimeError, match="boom"):
            await view.board_feed(websocket, "b")

    payload = json.loads(caplog.records[-1].message)
    assert payload["event"] == "ws_disconnect"
    assert "boom" in payload["reason"]
