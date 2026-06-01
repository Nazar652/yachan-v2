from pathlib import Path

from src.core.config import Settings


class LocalStorage:
    """Stores files on the local filesystem. Same surface a future object-store
    wrapper would expose, so FileService stays storage-agnostic."""

    def __init__(self, settings: Settings) -> None:
        self.base = Path(settings.storage_dir)
        self.base_url = settings.storage_base_url.rstrip("/")

    def _full_path(self, key: str) -> Path:
        return self.base / key

    def save(self, key: str, data: bytes) -> str:
        path = self._full_path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return key

    def read(self, key: str) -> bytes:
        return self._full_path(key).read_bytes()

    def delete(self, key: str) -> None:
        self._full_path(key).unlink(missing_ok=True)

    def exists(self, key: str) -> bool:
        return self._full_path(key).is_file()

    def public_url(self, key: str) -> str:
        return f"{self.base_url}/{key}"
