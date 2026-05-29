from unittest.mock import AsyncMock, MagicMock

from src.views.ws_view import WsView
from starlette.websockets import WebSocketDisconnect


async def test_forward_sends_only_message_type():
    async def listen():
        yield {"type": "subscribe", "data": 1}
        yield {"type": "message", "data": "payload"}

    pubsub = MagicMock()
    pubsub.listen = listen
    websocket = MagicMock()
    websocket.send_text = AsyncMock()

    await WsView._forward(pubsub, websocket)

    websocket.send_text.assert_awaited_once_with("payload")


async def test_drain_returns_on_disconnect():
    websocket = MagicMock()
    websocket.receive_text = AsyncMock(side_effect=WebSocketDisconnect(code=1000))

    await WsView._drain(websocket)  # returns without raising


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
