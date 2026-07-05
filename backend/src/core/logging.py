import json
import logging
from collections.abc import Mapping
from typing import Any

from src.utils.clock import utcnow
from src.utils.request_context import get_request_id

REDACTED = "<hidden>"

# header/body-field names never forwarded to logs (auth tokens, session cookies,
# captcha answers, mod passwords) even when the surrounding request/response is
# otherwise logged in full on a non-2xx status
SENSITIVE_HEADERS = {"authorization", "cookie", "set-cookie", "x-captcha-answer", "x-goog-api-key"}
SENSITIVE_BODY_FIELDS = {"password"}


def configure_logging(debug: bool) -> None:
    handler = logging.StreamHandler()
    # call sites format the full json line themselves (see log_event), so the
    # handler just writes the message as-is
    handler.setFormatter(logging.Formatter("%(message)s"))

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(logging.DEBUG if debug else logging.INFO)


def redact_headers(headers: Mapping[str, str]) -> dict[str, str]:
    return {
        key: REDACTED if key.lower() in SENSITIVE_HEADERS else value
        for key, value in headers.items()
    }


def redact_body(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: REDACTED if key.lower() in SENSITIVE_BODY_FIELDS else redact_body(item)
            for key, item in value.items()
        }

    if isinstance(value, list):
        return [redact_body(item) for item in value]

    return value


def log_event(logger: logging.Logger, event: str, level: int = logging.INFO, **fields: Any) -> None:
    payload = {
        "timestamp": utcnow().isoformat(),
        "event": event,
        "request_id": get_request_id(),
        **fields,
    }

    logger.log(level, json.dumps(payload, default=str))
