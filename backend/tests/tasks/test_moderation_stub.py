from unittest.mock import MagicMock

import src.tasks.moderation_stub as stub_module
from src.tasks.moderation_stub import moderate_image


def test_moderate_image_echoes_verdict_to_results_queue(monkeypatch):
    send_task = MagicMock()
    monkeypatch.setattr(stub_module.celery, "send_task", send_task)

    moderate_image(7, "http://minio:9000/yachan-media/abc.png", "nsfw")

    send_task.assert_called_once()
    assert send_task.call_args.args[0] == "apply_moderation_verdict"
    assert send_task.call_args.kwargs["queue"] == "moderation_results"
    assert send_task.call_args.kwargs["args"][0] == 7
    assert send_task.call_args.kwargs["args"][1]["status"] == "safe"
