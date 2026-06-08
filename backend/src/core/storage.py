import mimetypes
from abc import ABC, abstractmethod
from pathlib import Path

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from src.core.config import Settings


class Storage(ABC):
    """Storage surface shared by every backend. FileService and the views depend
    on this abstraction, never on a concrete backend, so the local filesystem and
    an object store (MinIO / S3) are interchangeable."""

    @abstractmethod
    def save(self, key: str, data: bytes) -> str: ...

    @abstractmethod
    def read(self, key: str) -> bytes: ...

    @abstractmethod
    def delete(self, key: str) -> None: ...

    @abstractmethod
    def exists(self, key: str) -> bool: ...

    @abstractmethod
    def public_url(self, key: str) -> str: ...


class LocalStorage(Storage):
    """Stores files on the local filesystem."""

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


class S3Storage(Storage):
    """Stores files in an S3-compatible object store. The same client talks to
    MinIO (via endpoint_url) in docker and to AWS S3 in production."""

    def __init__(self, settings: Settings) -> None:
        self.bucket = settings.s3_bucket
        self.base_url = settings.storage_base_url.rstrip("/")
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint_url or None,
            aws_access_key_id=settings.s3_access_key or None,
            aws_secret_access_key=settings.s3_secret_key or None,
            region_name=settings.s3_region,
            # path-style ("host/bucket/key") so a non-dns endpoint like minio:9000 works
            config=Config(s3={"addressing_style": "path"}),
        )

    def save(self, key: str, data: bytes) -> str:
        content_type = mimetypes.guess_type(key)[0] or "application/octet-stream"
        self.client.put_object(Bucket=self.bucket, Key=key, Body=data, ContentType=content_type)
        return key

    def read(self, key: str) -> bytes:
        response = self.client.get_object(Bucket=self.bucket, Key=key)
        return response["Body"].read()

    def delete(self, key: str) -> None:
        self.client.delete_object(Bucket=self.bucket, Key=key)

    def exists(self, key: str) -> bool:
        try:
            self.client.head_object(Bucket=self.bucket, Key=key)
        except ClientError:
            return False
        return True

    def public_url(self, key: str) -> str:
        return f"{self.base_url}/{key}"


def build_storage(settings: Settings) -> Storage:
    if settings.storage_backend == "s3":
        return S3Storage(settings)
    return LocalStorage(settings)
