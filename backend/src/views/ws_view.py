import asyncio

from kink import inject
from redis.asyncio import Redis
from starlette.websockets import WebSocket, WebSocketDisconnect

from src.utils.events import board_channel, thread_channel


class WsView:
    @inject
    def __init__(self, redis: Redis) -> None:
        self.redis = redis

    async def thread_feed(self, websocket: WebSocket, thread_id: int) -> None:
        await self._feed(websocket, thread_channel(thread_id))

    async def board_feed(self, websocket: WebSocket, board_slug: str) -> None:
        await self._feed(websocket, board_channel(board_slug))

    async def _feed(self, websocket: WebSocket, channel: str) -> None:
        await websocket.accept()
        pubsub = self.redis.pubsub()
        await pubsub.subscribe(channel)
        try:
            await self._pump(pubsub, websocket)
        finally:
            await pubsub.unsubscribe(channel)
            await pubsub.aclose()

    @staticmethod
    async def _pump(pubsub, websocket: WebSocket) -> None:
        # forward redis messages to the socket; stop as soon as the client drops
        forward = asyncio.create_task(WsView._forward(pubsub, websocket))
        drain = asyncio.create_task(WsView._drain(websocket))
        _done, pending = await asyncio.wait(
            {forward, drain}, return_when=asyncio.FIRST_COMPLETED
        )
        for task in pending:
            task.cancel()

    @staticmethod
    async def _forward(pubsub, websocket: WebSocket) -> None:
        async for message in pubsub.listen():
            if message.get("type") == "message":
                await websocket.send_text(message["data"])

    @staticmethod
    async def _drain(websocket: WebSocket) -> None:
        # we do not expect inbound messages; this just detects disconnect
        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            return
