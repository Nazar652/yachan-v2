import src.core.gemini as gemini_module
from src.core.gemini import GeminiClient, extract_text


def test_extract_text_joins_parts():
    payload = {"candidates": [{"content": {"parts": [{"text": "hello "}, {"text": "world"}]}}]}
    assert extract_text(payload) == "hello world"


def test_extract_text_empty_without_candidates():
    assert extract_text({"candidates": []}) == ""
    assert extract_text({}) == ""


class _FakeResponse:
    def __init__(self, data):
        self._data = data

    def raise_for_status(self):
        pass

    def json(self):
        return self._data


class _FakeClient:
    def __init__(self, data, captured):
        self._data = data
        self._captured = captured

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    async def post(self, url, headers=None, json=None):
        self._captured.update(url=url, headers=headers, json=json)
        return _FakeResponse(self._data)


async def test_generate_sends_prompt_and_returns_text(monkeypatch):
    captured: dict = {}
    data = {"candidates": [{"content": {"parts": [{"text": "a tl;dr"}]}}]}
    monkeypatch.setattr(
        gemini_module.httpx, "AsyncClient", lambda timeout: _FakeClient(data, captured)
    )

    client = GeminiClient(api_key="secret", model="gemini-3.1-flash-lite")
    result = await client.generate("summarize this")

    assert result == "a tl;dr"
    assert captured["headers"] == {"x-goog-api-key": "secret"}
    assert captured["json"]["contents"][0]["parts"][0]["text"] == "summarize this"
    assert "gemini-3.1-flash-lite:generateContent" in captured["url"]
