from unittest.mock import MagicMock

import app.tasks as tasks_module
from app.tasks import moderate_image, moderate_text


def test_moderate_image_sends_verdict(monkeypatch):
    monkeypatch.setattr(tasks_module, "fetch_bytes", lambda url: b"img")
    classifier = MagicMock()
    classifier.classify.return_value = {"status": "flagged", "nsfw_score": 0.8, "labels": None}
    monkeypatch.setattr(tasks_module, "get_classifier", lambda: classifier)
    send_task = MagicMock()
    monkeypatch.setattr(tasks_module.celery, "send_task", send_task)

    moderate_image(7, "http://minio:9000/yachan-media/x.png", "nsfw")

    send_task.assert_called_once()
    assert send_task.call_args.args[0] == "apply_moderation_verdict"
    assert send_task.call_args.kwargs["queue"] == "moderation_results"
    assert send_task.call_args.kwargs["args"][0] == 7
    assert send_task.call_args.kwargs["args"][1]["status"] == "flagged"


def test_moderate_image_flags_on_fetch_error(monkeypatch):
    def boom(url):
        raise RuntimeError("network down")

    monkeypatch.setattr(tasks_module, "fetch_bytes", boom)
    send_task = MagicMock()
    monkeypatch.setattr(tasks_module.celery, "send_task", send_task)

    moderate_image(7, "http://minio:9000/yachan-media/x.png", "nsfw")

    assert send_task.call_args.kwargs["args"][1]["status"] == "flagged"


def test_moderate_text_sends_verdict(monkeypatch):
    classifier = MagicMock()
    classifier.classify.return_value = {"toxic": True, "spam": False, "scores": {"toxic": 0.97}}
    monkeypatch.setattr(tasks_module, "get_text_classifier", lambda: classifier)
    send_task = MagicMock()
    monkeypatch.setattr(tasks_module.celery, "send_task", send_task)

    moderate_text(42, "some toxic text")

    send_task.assert_called_once()
    assert send_task.call_args.args[0] == "apply_text_verdict"
    assert send_task.call_args.kwargs["queue"] == "moderation_results"
    assert send_task.call_args.kwargs["args"] == [42, {"toxic": True, "spam": False, "scores": {"toxic": 0.97}}]


def test_moderate_text_does_not_flag_on_error(monkeypatch):
    def boom():
        raise RuntimeError("model missing")

    monkeypatch.setattr(tasks_module, "get_text_classifier", boom)
    send_task = MagicMock()
    monkeypatch.setattr(tasks_module.celery, "send_task", send_task)

    moderate_text(42, "text")

    verdict = send_task.call_args.kwargs["args"][1]
    assert verdict["toxic"] is False
    assert verdict["spam"] is False
