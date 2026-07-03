from unittest.mock import AsyncMock, MagicMock

from kink import di

from src.services.moderation_service import ModerationService
from src.services.report_service import ReportService
from src.tasks.moderation import apply_moderation_verdict, apply_text_verdict


def test_apply_moderation_verdict_delegates_to_service(monkeypatch):
    instance = MagicMock()
    instance.apply = AsyncMock()
    monkeypatch.setitem(di.factories, ModerationService, lambda container: instance)

    verdict = {"status": "blocked", "nsfw_score": 0.9}
    apply_moderation_verdict(7, verdict)

    instance.apply.assert_awaited_once_with(7, verdict)


def test_apply_text_verdict_delegates_to_report_service(monkeypatch):
    instance = MagicMock()
    instance.apply_text_verdict = AsyncMock()
    monkeypatch.setitem(di.factories, ReportService, lambda container: instance)

    verdict = {"toxic": True, "spam": False}
    apply_text_verdict(42, verdict)

    instance.apply_text_verdict.assert_awaited_once_with(42, verdict)
