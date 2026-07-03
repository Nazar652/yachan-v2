import json
from typing import Any

from redis.asyncio import Redis

# websocket event types pushed to subscribed clients
NEW_POST = "new_post"
POST_EDITED = "post_edited"
NEW_THREAD = "new_thread"
ATTACHMENT_MODERATED = "attachment_moderated"
THREAD_SUMMARIZED = "thread_summarized"
THREAD_UPDATED = "thread_updated"
THREAD_DELETED = "thread_deleted"


def thread_channel(thread_id: int) -> str:
    return f"ws:thread:{thread_id}"


def board_channel(board_slug: str) -> str:
    return f"ws:board:{board_slug}"


class EventPublisher:
    """Publishes realtime events to redis pub/sub channels."""

    def __init__(self, redis: Redis) -> None:
        self.redis = redis

    async def publish(self, channel: str, event_type: str, data: dict[str, Any]) -> None:
        await self.redis.publish(channel, json.dumps({"type": event_type, "data": data}))
