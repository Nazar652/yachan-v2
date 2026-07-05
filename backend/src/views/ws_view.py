import asyncio
import json
import logging
from time import perf_counter

from kink import inject
from redis import exceptions as redis_exceptions
from redis.asyncio import Redis
from starlette.websockets import WebSocket, WebSocketDisconnect

from src.core.logging import log_event
from src.utils.events import board_channel, thread_channel
from src.utils.request_context import new_id

logger = logging.getLogger("src.ws")


def event_type(data: str) -> str | None:
    try:
        return json.loads(data).get("type")
    except (ValueError, AttributeError):
        return None


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
        connection_id = new_id()
        start = perf_counter()
        log_event(logger, "ws_connect", connection_id=connection_id, channel=channel)

        pubsub = self.redis.pubsub()
        await pubsub.subscribe(channel)
        reason = "client_disconnect"
        try:
            await self._pump(pubsub, websocket, connection_id, channel)
        except Exception as exc:
            reason = f"error: {exc}"
            raise
        finally:
            await pubsub.unsubscribe(channel)
            await pubsub.aclose()
            log_event(
                logger,
                "ws_disconnect",
                connection_id=connection_id,
                channel=channel,
                reason=reason,
                duration_ms=round((perf_counter() - start) * 1000, 2),
            )

    @staticmethod
    async def _pump(pubsub, websocket: WebSocket, connection_id: str, channel: str) -> None:
        forward = asyncio.create_task(WsView._forward(pubsub, websocket, connection_id, channel))
        drain = asyncio.create_task(WsView._drain(websocket, connection_id, channel))

        done, pending = await asyncio.wait(
            {forward, drain}, return_when=asyncio.FIRST_COMPLETED
        )

        for task in pending:
            task.cancel()
        for task in done:
            task.result()

    @staticmethod
    async def _forward(pubsub, websocket: WebSocket, connection_id: str, channel: str) -> None:
        # redis gives pubsub connections a 5s socket_timeout by default, so an idle
        # listen() raises redis TimeoutError every 5s. swallow it and keep listening;
        # note redis.exceptions.TimeoutError is not the builtin TimeoutError.
        while True:
            try:
                async for message in pubsub.listen():
                    if message.get("type") == "message":
                        data = message["data"]
                        log_event(
                            logger,
                            "ws_message_out",
                            connection_id=connection_id,
                            channel=channel,
                            event_type=event_type(data),
                            body=data,
                        )
                        await websocket.send_text(data)
                break
            except redis_exceptions.TimeoutError:
                continue

    @staticmethod
    async def _drain(websocket: WebSocket, connection_id: str, channel: str) -> None:
        # we do not expect a meaningful inbound message; this loop mainly detects
        # disconnect, but anything a client does send is still logged as it arrives
        try:
            while True:
                text = await websocket.receive_text()
                log_event(
                    logger,
                    "ws_message_in",
                    connection_id=connection_id,
                    channel=channel,
                    body=text,
                )
        except WebSocketDisconnect:
            return
