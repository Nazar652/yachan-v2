import json
import logging
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from src.core.storage import LocalStorage, S3Storage, build_storage


def _storage(tmp_path):
    settings = SimpleNamespace(storage_dir=str(tmp_path), storage_base_url="/media/")
    return LocalStorage(settings)


def _s3_settings():
    return SimpleNamespace(
        s3_bucket="media",
        storage_base_url="/media/",
        s3_endpoint_url="http://minio:9000",
        s3_access_key="key",
        s3_secret_key="secret",
        s3_region="us-east-1",
    )


def _async_cm(value):
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=value)
    cm.__aexit__ = AsyncMock(return_value=False)
    return cm


def _s3_storage():
    """Returns (storage, client). The aioboto3 session is mocked so `session.client(...)`
    yields the returned client as an async context manager."""
    client = MagicMock()
    client.put_object = AsyncMock()
    client.get_object = AsyncMock()
    client.delete_object = AsyncMock()
    client.head_object = AsyncMock()
    session = MagicMock()
    session.client = MagicMock(return_value=_async_cm(client))
    with patch("src.core.storage.aioboto3.Session", return_value=session):
        storage = S3Storage(_s3_settings())
    return storage, client


async def test_save_and_read_roundtrip(tmp_path):
    storage = _storage(tmp_path)
    key = await storage.save("a/b/file.bin", b"data")
    assert key == "a/b/file.bin"
    assert await storage.read("a/b/file.bin") == b"data"


async def test_exists(tmp_path):
    storage = _storage(tmp_path)
    assert await storage.exists("missing") is False
    await storage.save("here.txt", b"x")
    assert await storage.exists("here.txt") is True


async def test_delete_is_idempotent(tmp_path):
    storage = _storage(tmp_path)
    await storage.save("f.txt", b"x")
    await storage.delete("f.txt")
    assert await storage.exists("f.txt") is False
    await storage.delete("f.txt")  # no error on missing


def test_public_url_strips_trailing_slash(tmp_path):
    storage = _storage(tmp_path)
    assert storage.public_url("a/b.png") == "/media/a/b.png"


async def test_s3_save_puts_object_with_guessed_content_type():
    storage, client = _s3_storage()
    key = await storage.save("abc.png", b"data")
    assert key == "abc.png"
    client.put_object.assert_awaited_once_with(
        Bucket="media", Key="abc.png", Body=b"data", ContentType="image/png"
    )


async def test_s3_save_falls_back_to_octet_stream():
    storage, client = _s3_storage()
    await storage.save("noext", b"x")
    assert client.put_object.await_args.kwargs["ContentType"] == "application/octet-stream"


async def test_s3_read_returns_body_bytes():
    storage, client = _s3_storage()
    stream = MagicMock()
    stream.read = AsyncMock(return_value=b"bytes")
    client.get_object.return_value = {"Body": _async_cm(stream)}
    assert await storage.read("k") == b"bytes"
    client.get_object.assert_awaited_once_with(Bucket="media", Key="k")


async def test_s3_delete_calls_delete_object():
    storage, client = _s3_storage()
    await storage.delete("k")
    client.delete_object.assert_awaited_once_with(Bucket="media", Key="k")


async def test_s3_exists_true_when_head_succeeds():
    storage, client = _s3_storage()
    assert await storage.exists("k") is True
    client.head_object.assert_awaited_once_with(Bucket="media", Key="k")


async def test_s3_exists_false_on_client_error():
    storage, client = _s3_storage()
    client.head_object.side_effect = ClientError({"Error": {"Code": "404"}}, "HeadObject")
    assert await storage.exists("missing") is False


async def test_s3_save_logs_external_call(caplog):
    storage, _ = _s3_storage()
    with caplog.at_level(logging.INFO, logger="src.external"):
        await storage.save("abc.png", b"data")

    payload = json.loads(caplog.records[-1].message)
    assert payload["event"] == "external_call"
    assert payload["target"] == "s3"
    assert payload["operation"] == "save"
    assert payload["bucket"] == "media"
    assert payload["key"] == "abc.png"
    assert payload["error"] is None


async def test_s3_save_logs_error_and_reraises(caplog):
    storage, client = _s3_storage()
    client.put_object.side_effect = ClientError({"Error": {"Code": "500"}}, "PutObject")

    with caplog.at_level(logging.INFO, logger="src.external"), pytest.raises(ClientError):
        await storage.save("abc.png", b"data")

    payload = json.loads(caplog.records[-1].message)
    assert payload["operation"] == "save"
    assert "500" in payload["error"]


async def test_s3_exists_logs_exists_field(caplog):
    storage, client = _s3_storage()
    client.head_object.side_effect = ClientError({"Error": {"Code": "404"}}, "HeadObject")

    with caplog.at_level(logging.INFO, logger="src.external"):
        await storage.exists("missing")

    payload = json.loads(caplog.records[-1].message)
    assert payload["operation"] == "exists"
    assert payload["exists"] is False


def test_s3_public_url_strips_trailing_slash():
    storage, _ = _s3_storage()
    assert storage.public_url("a/b.png") == "/media/a/b.png"


def test_build_storage_returns_local_by_default(tmp_path):
    settings = SimpleNamespace(
        storage_backend="local", storage_dir=str(tmp_path), storage_base_url="/media"
    )
    assert isinstance(build_storage(settings), LocalStorage)


def test_build_storage_returns_s3_when_selected():
    settings = _s3_settings()
    settings.storage_backend = "s3"
    with patch("src.core.storage.aioboto3.Session", return_value=MagicMock()):
        assert isinstance(build_storage(settings), S3Storage)
