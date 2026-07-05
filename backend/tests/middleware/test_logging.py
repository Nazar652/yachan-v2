import json
import logging

from src.middleware.logging import LoggingMiddleware, summarize_body
from src.utils.request_context import get_request_id


def _receive_queue(messages):
    messages = list(messages)

    async def receive():
        return messages.pop(0)

    return receive


def _collect_send():
    sent: list[dict] = []

    async def send(message):
        sent.append(message)

    return send, sent


def _http_scope(headers=None, method="GET", path="/api/boards", query=b""):
    return {
        "type": "http",
        "method": method,
        "path": path,
        "query_string": query,
        "headers": headers or [],
    }


def _responding_app(status: int, body: bytes):
    async def app(scope, receive, send):
        await receive()
        await send(
            {
                "type": "http.response.start",
                "status": status,
                "headers": [(b"content-type", b"application/json")],
            }
        )
        await send({"type": "http.response.body", "body": body})

    return app


def test_summarize_body_returns_none_for_empty():
    assert summarize_body(b"", 0, "application/json", True) is None


def test_summarize_body_parses_json_when_include_full():
    assert summarize_body(b'{"a": 1}', 8, "application/json", True) == {"a": 1}


def test_summarize_body_falls_back_to_raw_text_on_invalid_json():
    assert summarize_body(b"not json", 8, "application/json", True) == "not json"


def test_summarize_body_falls_back_to_size_when_not_text():
    assert summarize_body(b"\xff\xfe\x00\x01", 4, "application/json", True) == {"size": 4}


def test_summarize_body_returns_text_for_plain_text():
    assert summarize_body(b"hello", 5, "text/plain", True) == "hello"


def test_summarize_body_hides_content_when_not_include_full():
    assert summarize_body(b'{"a": 1}', 8, "application/json", False) == {"size": 8}


def test_summarize_body_multipart_never_returns_content():
    result = summarize_body(b"", 1234, "multipart/form-data; boundary=x", True)
    assert result == {"content_type": "multipart/form-data; boundary=x", "size": 1234}


async def test_non_http_scope_passes_through_untouched():
    calls = []

    async def app(scope, receive, send):
        calls.append(scope)

    send, _ = _collect_send()
    middleware = LoggingMiddleware(app)
    await middleware({"type": "lifespan"}, _receive_queue([]), send)

    assert calls == [{"type": "lifespan"}]


async def test_logs_full_body_on_non_2xx_status(caplog):
    request_body = json.dumps({"reason": "spam"}).encode()
    response_body = json.dumps({"detail": "not found"}).encode()
    scope = _http_scope(
        headers=[(b"content-type", b"application/json")], method="POST", path="/api/x"
    )
    receive = _receive_queue([{"type": "http.request", "body": request_body, "more_body": False}])
    send, _ = _collect_send()
    app = _responding_app(404, response_body)

    with caplog.at_level(logging.INFO, logger="src.http"):
        await LoggingMiddleware(app)(scope, receive, send)

    payload = json.loads(caplog.records[-1].message)
    assert payload["event"] == "http_request"
    assert payload["status_code"] == 404
    assert payload["method"] == "POST"
    assert payload["path"] == "/api/x"
    assert payload["request_body"] == {"reason": "spam"}
    assert payload["response_body"] == {"detail": "not found"}


async def test_logs_size_only_on_2xx_status(caplog):
    request_body = json.dumps({"title": "hello"}).encode()
    response_body = json.dumps({"id": 1}).encode()
    scope = _http_scope(headers=[(b"content-type", b"application/json")], method="POST")
    receive = _receive_queue([{"type": "http.request", "body": request_body, "more_body": False}])
    send, _ = _collect_send()
    app = _responding_app(201, response_body)

    with caplog.at_level(logging.INFO, logger="src.http"):
        await LoggingMiddleware(app)(scope, receive, send)

    payload = json.loads(caplog.records[-1].message)
    assert payload["status_code"] == 201
    assert payload["request_body"] == {"size": len(request_body)}
    assert payload["response_body"] == {"size": len(response_body)}


async def test_redacts_password_field_in_non_2xx_json_body(caplog):
    # a wrong mod login answers 401 with the request body echoed by the non-2xx
    # rule; the password must never reach the log even then (see ModLogin schema)
    request_body = json.dumps({"username": "admin", "password": "super-secret-guess"}).encode()
    scope = _http_scope(
        headers=[(b"content-type", b"application/json")], method="POST", path="/api/mod/login"
    )
    receive = _receive_queue([{"type": "http.request", "body": request_body, "more_body": False}])
    send, _ = _collect_send()
    app = _responding_app(401, b"")

    with caplog.at_level(logging.INFO, logger="src.http"):
        await LoggingMiddleware(app)(scope, receive, send)

    payload = json.loads(caplog.records[-1].message)
    assert payload["request_body"] == {"username": "admin", "password": "<hidden>"}
    assert "super-secret-guess" not in caplog.text


async def test_redacts_sensitive_request_headers(caplog):
    scope = _http_scope(
        headers=[(b"authorization", b"Bearer secret"), (b"content-type", b"text/plain")]
    )
    receive = _receive_queue([{"type": "http.request", "body": b"", "more_body": False}])
    send, _ = _collect_send()
    app = _responding_app(200, b"")

    with caplog.at_level(logging.INFO, logger="src.http"):
        await LoggingMiddleware(app)(scope, receive, send)

    payload = json.loads(caplog.records[-1].message)
    assert payload["headers"]["authorization"] == "<hidden>"


async def test_multipart_request_body_logs_size_not_content(caplog):
    body = b"--xyz\r\nfake file bytes\r\n--xyz--"
    scope = _http_scope(
        headers=[(b"content-type", b"multipart/form-data; boundary=xyz")], method="POST"
    )
    receive = _receive_queue([{"type": "http.request", "body": body, "more_body": False}])
    send, _ = _collect_send()
    app = _responding_app(400, b"")

    with caplog.at_level(logging.INFO, logger="src.http"):
        await LoggingMiddleware(app)(scope, receive, send)

    payload = json.loads(caplog.records[-1].message)
    assert payload["request_body"] == {
        "content_type": "multipart/form-data; boundary=xyz",
        "size": len(body),
    }


async def test_sets_request_id_during_request_and_clears_after():
    seen = {}

    async def app(scope, receive, send):
        await receive()
        seen["request_id"] = get_request_id()
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b""})

    scope = _http_scope()
    receive = _receive_queue([{"type": "http.request", "body": b"", "more_body": False}])
    send, _ = _collect_send()

    await LoggingMiddleware(app)(scope, receive, send)

    assert seen["request_id"] is not None
    assert get_request_id() is None
