import json
import logging

from src.core.logging import (
    REDACTED,
    configure_logging,
    log_event,
    redact_body,
    redact_headers,
)
from src.utils.request_context import set_request_id


def test_redact_headers_hides_sensitive_values_case_insensitive():
    headers = {"Authorization": "Bearer secret", "Content-Type": "application/json"}
    redacted = redact_headers(headers)
    assert redacted["Authorization"] == REDACTED
    assert redacted["Content-Type"] == "application/json"


def test_redact_headers_covers_cookies_and_captcha_answer():
    headers = {"Cookie": "session=1", "Set-Cookie": "session=1", "X-Captcha-Answer": "42"}
    redacted = redact_headers(headers)
    assert all(value == REDACTED for value in redacted.values())


def test_redact_body_hides_password_field():
    body = {"username": "mod", "password": "hunter2"}
    redacted = redact_body(body)
    assert redacted == {"username": "mod", "password": REDACTED}


def test_redact_body_recurses_into_nested_dicts_and_lists():
    body = {"users": [{"password": "a"}, {"password": "b"}]}
    redacted = redact_body(body)
    assert redacted == {"users": [{"password": REDACTED}, {"password": REDACTED}]}


def test_redact_body_passes_through_non_dict_values():
    assert redact_body("plain text") == "plain text"
    assert redact_body(None) is None


def test_log_event_emits_json_with_request_id_and_fields(caplog):
    set_request_id("req-1")
    logger = logging.getLogger("test.logging")
    with caplog.at_level(logging.INFO, logger="test.logging"):
        log_event(logger, "http_request", status_code=200, duration_ms=1.5)
    set_request_id(None)

    payload = json.loads(caplog.records[0].message)
    assert payload["event"] == "http_request"
    assert payload["request_id"] == "req-1"
    assert payload["status_code"] == 200
    assert payload["duration_ms"] == 1.5
    assert "timestamp" in payload


def test_log_event_defaults_to_info_level(caplog):
    logger = logging.getLogger("test.logging.level")
    with caplog.at_level(logging.DEBUG, logger="test.logging.level"):
        log_event(logger, "task_invoked")

    assert caplog.records[0].levelno == logging.INFO


def test_configure_logging_sets_debug_level():
    configure_logging(debug=True)
    assert logging.getLogger().level == logging.DEBUG


def test_configure_logging_sets_info_level_by_default():
    configure_logging(debug=False)
    assert logging.getLogger().level == logging.INFO
