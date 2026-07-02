from unittest.mock import MagicMock

import app.fetch as fetch_module
from app.fetch import fetch_bytes


def test_fetch_bytes_returns_content(monkeypatch):
    response = MagicMock()
    response.content = b"bytes"
    monkeypatch.setattr(fetch_module.httpx, "get", MagicMock(return_value=response))

    assert fetch_bytes("http://minio:9000/yachan-media/x.png") == b"bytes"
    response.raise_for_status.assert_called_once()
