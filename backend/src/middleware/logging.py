import json
import logging
from time import perf_counter
from typing import Any

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from src.core.logging import log_event, redact_body, redact_headers
from src.utils.request_context import new_id, set_request_id

logger = logging.getLogger("src.http")


def _decode_headers(raw_headers: list[tuple[bytes, bytes]]) -> dict[str, str]:
    return {key.decode("latin-1"): value.decode("latin-1") for key, value in raw_headers}


def summarize_body(raw: bytes, size: int, content_type: str, include_full: bool) -> Any:
    if size == 0:
        return None

    # attachments are binary and can be several mb each; only their byte count is
    # ever useful in a log line, so LoggingMiddleware never buffers their bytes
    if content_type.startswith("multipart/form-data"):
        return {"content_type": content_type, "size": size}

    if not include_full:
        return {"size": size}

    if content_type.startswith("application/json"):
        try:
            return redact_body(json.loads(raw))
        except ValueError:
            pass

    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        pass

    return {"size": size}


class LoggingMiddleware:
    """Logs one structured `http_request` event per request, combining the
    incoming request and outgoing response (they always pair 1:1, so one line
    correlated by request_id says more than two). Body text is included in full
    only on a non-2xx status; multipart bodies never get their bytes buffered."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        set_request_id(new_id())
        start = perf_counter()

        request_headers = _decode_headers(scope.get("headers", []))
        request_content_type = request_headers.get("content-type", "")
        is_multipart = request_content_type.startswith("multipart/form-data")
        request_body = bytearray()
        request_size = 0

        async def receiving() -> Message:
            nonlocal request_size
            message = await receive()

            if message["type"] == "http.request":
                chunk = message.get("body", b"")
                request_size += len(chunk)
                if not is_multipart:
                    request_body.extend(chunk)

            return message

        status_code = 500
        response_headers: dict[str, str] = {}
        response_body = bytearray()

        async def sending(message: Message) -> None:
            nonlocal status_code, response_headers
            if message["type"] == "http.response.start":
                status_code = message["status"]
                response_headers = _decode_headers(message.get("headers", []))
            elif message["type"] == "http.response.body":
                response_body.extend(message.get("body", b""))

            await send(message)

        try:
            await self.app(scope, receiving, sending)
        finally:
            is_success = 200 <= status_code < 300

            log_event(
                logger,
                "http_request",
                method=scope["method"],
                path=scope["path"],
                query=scope.get("query_string", b"").decode("latin-1"),
                headers=redact_headers(request_headers),
                request_body=summarize_body(
                    bytes(request_body), request_size, request_content_type, not is_success
                ),
                status_code=status_code,
                duration_ms=round((perf_counter() - start) * 1000, 2),
                response_body=summarize_body(
                    bytes(response_body),
                    len(response_body),
                    response_headers.get("content-type", ""),
                    not is_success,
                ),
            )

            set_request_id(None)
