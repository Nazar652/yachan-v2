from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

from src.models.attachment import ModerationStatus
from src.services.moderation_service import ModerationService


def _service(attachment=None, post=None):
    attachment_repo = MagicMock()
    attachment_repo.set_moderation = AsyncMock()
    attachment_repo.get_by_id = AsyncMock(return_value=attachment)
    post_repo = MagicMock()
    post_repo.get_by_id = AsyncMock(return_value=post)
    events = MagicMock()
    events.publish = AsyncMock()
    service = ModerationService(attachment_repo=attachment_repo, post_repo=post_repo, events=events)
    return service, attachment_repo, events


async def test_apply_maps_verdict_to_set_moderation():
    service, attachment_repo, _ = _service(
        attachment=SimpleNamespace(post_id=10), post=SimpleNamespace(thread_id=5)
    )

    await service.apply(7, {"status": "blocked", "nsfw_score": 0.9, "labels": None})

    attachment_repo.set_moderation.assert_awaited_once_with(
        7, status=ModerationStatus.BLOCKED, nsfw_score=0.9
    )


async def test_apply_defaults_missing_score_to_none():
    service, attachment_repo, _ = _service(
        attachment=SimpleNamespace(post_id=10), post=SimpleNamespace(thread_id=5)
    )

    await service.apply(7, {"status": "safe"})

    attachment_repo.set_moderation.assert_awaited_once_with(
        7, status=ModerationStatus.SAFE, nsfw_score=None
    )


async def test_apply_publishes_ws_event_to_thread():
    service, _, events = _service(
        attachment=SimpleNamespace(post_id=10), post=SimpleNamespace(thread_id=5)
    )

    await service.apply(7, {"status": "flagged", "nsfw_score": 0.5})

    events.publish.assert_awaited_once()
    channel, event_type, data = events.publish.await_args.args
    assert channel == "ws:thread:5"
    assert event_type == "attachment_moderated"
    assert data == {"attachment_id": 7, "post_id": 10, "moderation_status": "flagged"}


async def test_apply_skips_ws_when_attachment_missing():
    service, _, events = _service(attachment=None)

    await service.apply(7, {"status": "safe"})

    events.publish.assert_not_awaited()
