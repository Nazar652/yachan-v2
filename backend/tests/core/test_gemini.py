import json
import logging

import pytest

import src.core.gemini as gemini_module
from src.core.gemini import GeminiClient, extract_text


def test_extract_text_joins_parts():
    payload = {"candidates": [{"content": {"parts": [{"text": "hello "}, {"text": "world"}]}}]}
    assert extract_text(payload) == "hello world"


def test_extract_text_empty_without_candidates():
    assert extract_text({"candidates": []}) == ""
    assert extract_text({}) == ""


class _FakeResponse:
    def __init__(self, data, status_code=200):
        self._data = data
        self.status_code = status_code
        self.text = json.dumps(data)

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"status {self.status_code}")

    def json(self):
        return self._data


class _FakeClient:
    def __init__(self, response, captured):
        self._response = response
        self._captured = captured

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    async def post(self, url, headers=None, json=None):
        self._captured.update(url=url, headers=headers, json=json)
        return self._response


async def test_generate_sends_prompt_and_returns_text(monkeypatch):
    captured: dict = {}
    data = {"candidates": [{"content": {"parts": [{"text": "a tl;dr"}]}}]}
    monkeypatch.setattr(
        gemini_module.httpx,
        "AsyncClient",
        lambda timeout: _FakeClient(_FakeResponse(data), captured),
    )

    client = GeminiClient(api_key="secret", model="gemini-3.1-flash-lite")
    result = await client.generate("summarize this")

    assert result == "a tl;dr"
    assert captured["headers"] == {"x-goog-api-key": "secret"}
    assert captured["json"]["contents"][0]["parts"][0]["text"] == "summarize this"
    assert "gemini-3.1-flash-lite:generateContent" in captured["url"]


async def test_generate_logs_redacted_headers_and_size_only_on_success(monkeypatch, caplog):
    captured: dict = {}
    data = {"candidates": [{"content": {"parts": [{"text": "ok"}]}}]}
    monkeypatch.setattr(
        gemini_module.httpx,
        "AsyncClient",
        lambda timeout: _FakeClient(_FakeResponse(data), captured),
    )

    client = GeminiClient(api_key="secret", model="gemini-3.1-flash-lite")
    with caplog.at_level(logging.INFO, logger="src.external"):
        await client.generate("summarize this")

    payload = json.loads(caplog.records[-1].message)
    assert payload["event"] == "external_call"
    assert payload["target"] == "gemini"
    assert payload["headers"]["x-goog-api-key"] == "<hidden>"
    assert payload["status_code"] == 200
    assert payload["response_body"] == {"size": len(json.dumps(data))}


async def test_generate_logs_full_body_on_error_and_reraises(monkeypatch, caplog):
    captured: dict = {}
    error_data = {"error": {"message": "bad request"}}
    monkeypatch.setattr(
        gemini_module.httpx,
        "AsyncClient",
        lambda timeout: _FakeClient(_FakeResponse(error_data, status_code=400), captured),
    )

    client = GeminiClient(api_key="secret", model="gemini-3.1-flash-lite")
    with caplog.at_level(logging.INFO, logger="src.external"), pytest.raises(RuntimeError):
        await client.generate("summarize this")

    payload = json.loads(caplog.records[-1].message)
    assert payload["status_code"] == 400
    assert payload["response_body"] == json.dumps(error_data)
