import json
import logging

from src.celery_app import _log_task_enqueued
from src.utils.request_context import set_request_id


def test_beat_scheduled_tasks_are_registered():
    from src.celery_app import celery

    # import_default_modules() is the include-import step a worker runs on start;
    # the tasks beat references by name must end up registered.
    celery.loader.import_default_modules()

    assert "expire_bans" in celery.tasks
    assert "process_attachment" in celery.tasks
    assert "apply_moderation_verdict" in celery.tasks
    assert "apply_text_verdict" in celery.tasks
    assert "summarize_thread" in celery.tasks
    assert "summarize_stale_threads" in celery.tasks


def test_before_task_publish_stamps_request_id_onto_headers():
    set_request_id("req-42")
    headers = {"id": "task-1"}
    _log_task_enqueued(sender="process_attachment", headers=headers, routing_key="celery")
    set_request_id(None)

    assert headers["request_id"] == "req-42"


def test_before_task_publish_logs_task_enqueued(caplog):
    headers = {"id": "task-1"}
    with caplog.at_level(logging.INFO, logger="src.tasks"):
        _log_task_enqueued(sender="process_attachment", headers=headers, routing_key="celery")

    payload = json.loads(caplog.records[-1].message)
    assert payload["event"] == "task_enqueued"
    assert payload["task_name"] == "process_attachment"
    assert payload["task_id"] == "task-1"
    assert payload["queue"] == "celery"


def test_before_task_publish_handles_missing_headers(caplog):
    with caplog.at_level(logging.INFO, logger="src.tasks"):
        _log_task_enqueued(sender="process_attachment", headers=None, routing_key="moderation")

    payload = json.loads(caplog.records[-1].message)
    assert payload["task_id"] is None
