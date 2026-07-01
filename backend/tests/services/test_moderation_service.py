from unittest.mock import AsyncMock, MagicMock

from src.models.attachment import ModerationStatus
from src.services.moderation_service import ModerationService


async def test_apply_maps_verdict_to_set_moderation():
    repo = MagicMock()
    repo.set_moderation = AsyncMock()
    service = ModerationService(attachment_repo=repo)

    await service.apply(7, {"status": "blocked", "nsfw_score": 0.9, "labels": None})

    repo.set_moderation.assert_awaited_once_with(
        7, status=ModerationStatus.BLOCKED, nsfw_score=0.9
    )


async def test_apply_defaults_missing_score_to_none():
    repo = MagicMock()
    repo.set_moderation = AsyncMock()
    service = ModerationService(attachment_repo=repo)

    await service.apply(7, {"status": "safe"})

    repo.set_moderation.assert_awaited_once_with(
        7, status=ModerationStatus.SAFE, nsfw_score=None
    )
