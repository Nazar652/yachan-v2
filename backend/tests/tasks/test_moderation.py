from unittest.mock import AsyncMock, MagicMock

import src.tasks.moderation as moderation_task
from src.tasks.moderation import apply_moderation_verdict


def test_apply_moderation_verdict_delegates_to_service(monkeypatch):
    instance = MagicMock()
    instance.apply = AsyncMock()
    monkeypatch.setattr(moderation_task, "get_dependency", lambda cls: instance)

    verdict = {"status": "blocked", "nsfw_score": 0.9}
    apply_moderation_verdict(7, verdict)

    instance.apply.assert_awaited_once_with(7, verdict)
