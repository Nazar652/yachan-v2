from unittest.mock import MagicMock

import app.fetch as fetch_module
from app.fetch import fetch_bytes


def test_fetch_bytes_returns_content(monkeypatch):
    response = MagicMock()
    response.content = b"bytes"
    get = MagicMock(return_value=response)
    monkeypatch.setattr(fetch_module.httpx, "get", get)

    assert fetch_bytes("http://minio:9000/yachan-media/x.png") == b"bytes"
    response.raise_for_status.assert_called_once()
    # redirects are not followed, so a redirecting host cannot steer the fetch
    assert get.call_args.kwargs["follow_redirects"] is False
