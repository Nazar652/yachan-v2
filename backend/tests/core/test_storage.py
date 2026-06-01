from types import SimpleNamespace

from src.core.storage import LocalStorage


def _storage(tmp_path):
    settings = SimpleNamespace(storage_dir=str(tmp_path), storage_base_url="/media/")
    return LocalStorage(settings)


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
