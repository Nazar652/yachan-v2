from unittest.mock import MagicMock

import app.tasks as tasks_module
from app.tasks import moderate_image


def test_moderate_image_sends_verdict(monkeypatch):
    monkeypatch.setattr(tasks_module, "fetch_bytes", lambda url: b"img")
    monkeypatch.setattr(
        tasks_module.classifier,
        "classify",
        lambda data, mode: {"status": "safe", "nsfw_score": 0.0, "labels": None},
    )
    send_task = MagicMock()
    monkeypatch.setattr(tasks_module.celery, "send_task", send_task)

    moderate_image(7, "http://minio:9000/yachan-media/x.png", "nsfw")

    send_task.assert_called_once()
    assert send_task.call_args.args[0] == "apply_moderation_verdict"
    assert send_task.call_args.kwargs["queue"] == "moderation_results"
    assert send_task.call_args.kwargs["args"][0] == 7
    assert send_task.call_args.kwargs["args"][1]["status"] == "safe"


def test_moderate_image_flags_on_fetch_error(monkeypatch):
    def boom(url):
        raise RuntimeError("network down")

    monkeypatch.setattr(tasks_module, "fetch_bytes", boom)
    send_task = MagicMock()
    monkeypatch.setattr(tasks_module.celery, "send_task", send_task)

    moderate_image(7, "http://minio:9000/yachan-media/x.png", "nsfw")

    assert send_task.call_args.kwargs["args"][1]["status"] == "flagged"
