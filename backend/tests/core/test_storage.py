from types import SimpleNamespace
from unittest.mock import MagicMock, patch

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


def _s3_storage():
    with patch("src.core.storage.boto3.client", return_value=MagicMock()):
        return S3Storage(_s3_settings())


def test_save_and_read_roundtrip(tmp_path):
    storage = _storage(tmp_path)
    key = storage.save("a/b/file.bin", b"data")
    assert key == "a/b/file.bin"
    assert storage.read("a/b/file.bin") == b"data"


def test_exists(tmp_path):
    storage = _storage(tmp_path)
    assert storage.exists("missing") is False
    storage.save("here.txt", b"x")
    assert storage.exists("here.txt") is True


def test_delete_is_idempotent(tmp_path):
    storage = _storage(tmp_path)
    storage.save("f.txt", b"x")
    storage.delete("f.txt")
    assert storage.exists("f.txt") is False
    storage.delete("f.txt")  # no error on missing


def test_public_url_strips_trailing_slash(tmp_path):
    storage = _storage(tmp_path)
    assert storage.public_url("a/b.png") == "/media/a/b.png"


def test_s3_save_puts_object_with_guessed_content_type():
    storage = _s3_storage()
    key = storage.save("abc.png", b"data")
    assert key == "abc.png"
    storage.client.put_object.assert_called_once_with(
        Bucket="media", Key="abc.png", Body=b"data", ContentType="image/png"
    )


def test_s3_save_falls_back_to_octet_stream():
    storage = _s3_storage()
    storage.save("noext", b"x")
    assert storage.client.put_object.call_args.kwargs["ContentType"] == "application/octet-stream"


def test_s3_read_returns_body_bytes():
    storage = _s3_storage()
    storage.client.get_object.return_value = {"Body": MagicMock(read=lambda: b"bytes")}
    assert storage.read("k") == b"bytes"
    storage.client.get_object.assert_called_once_with(Bucket="media", Key="k")


def test_s3_delete_calls_delete_object():
    storage = _s3_storage()
    storage.delete("k")
    storage.client.delete_object.assert_called_once_with(Bucket="media", Key="k")


def test_s3_exists_true_when_head_succeeds():
    storage = _s3_storage()
    assert storage.exists("k") is True
    storage.client.head_object.assert_called_once_with(Bucket="media", Key="k")


def test_s3_exists_false_on_client_error():
    storage = _s3_storage()
    storage.client.head_object.side_effect = ClientError(
        {"Error": {"Code": "404"}}, "HeadObject"
    )
    assert storage.exists("missing") is False


def test_s3_public_url_strips_trailing_slash():
    storage = _s3_storage()
    assert storage.public_url("a/b.png") == "/media/a/b.png"


def test_build_storage_returns_local_by_default(tmp_path):
    settings = SimpleNamespace(
        storage_backend="local", storage_dir=str(tmp_path), storage_base_url="/media"
    )
    assert isinstance(build_storage(settings), LocalStorage)


def test_build_storage_returns_s3_when_selected():
    settings = _s3_settings()
    settings.storage_backend = "s3"
    with patch("src.core.storage.boto3.client", return_value=MagicMock()):
        assert isinstance(build_storage(settings), S3Storage)
