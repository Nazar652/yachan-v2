import mimetypes
from abc import ABC, abstractmethod
from pathlib import Path

import aioboto3
import anyio.to_thread
from aiobotocore.config import AioConfig
from botocore.exceptions import ClientError

from src.core.config import Settings


class Storage(ABC):
    """Storage surface shared by every backend. FileService and the views depend
    on this abstraction, never on a concrete backend, so the local filesystem and
    an object store (MinIO / S3) are interchangeable. The io methods are async so
    a request never blocks the event loop on disk or network."""

    @abstractmethod
    async def save(self, key: str, data: bytes) -> str: ...

    @abstractmethod
    async def read(self, key: str) -> bytes: ...

    @abstractmethod
    async def delete(self, key: str) -> None: ...

    @abstractmethod
    async def exists(self, key: str) -> bool: ...

    @abstractmethod
    def public_url(self, key: str) -> str: ...


class LocalStorage(Storage):
    """Stores files on the local filesystem. Blocking disk io is offloaded to a
    worker thread so it never stalls the event loop."""

    def __init__(self, settings: Settings) -> None:
        self.base = Path(settings.storage_dir)
        self.base_url = settings.storage_base_url.rstrip("/")

    def _full_path(self, key: str) -> Path:
        return self.base / key

    def _write(self, key: str, data: bytes) -> None:
        path = self._full_path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def _delete(self, key: str) -> None:
        self._full_path(key).unlink(missing_ok=True)

    async def save(self, key: str, data: bytes) -> str:
        await anyio.to_thread.run_sync(self._write, key, data)
        return key

    async def read(self, key: str) -> bytes:
        return await anyio.to_thread.run_sync(self._full_path(key).read_bytes)

    async def delete(self, key: str) -> None:
        await anyio.to_thread.run_sync(self._delete, key)

    async def exists(self, key: str) -> bool:
        return await anyio.to_thread.run_sync(self._full_path(key).is_file)

    def public_url(self, key: str) -> str:
        return f"{self.base_url}/{key}"


class S3Storage(Storage):
    """Stores files in an S3-compatible object store via aioboto3. The same client
    talks to MinIO (via endpoint_url) in docker and to AWS S3 in production. A
    fresh client is opened per operation — aioboto3 clients are async context
    managers bound to the running loop, so they are not held as singletons."""

    def __init__(self, settings: Settings) -> None:
        self.bucket = settings.s3_bucket
        self.base_url = settings.storage_base_url.rstrip("/")
        self.session = aioboto3.Session()
        self.endpoint_url = settings.s3_endpoint_url or None
        self.access_key = settings.s3_access_key or None
        self.secret_key = settings.s3_secret_key or None
        self.region = settings.s3_region

        # path-style ("host/bucket/key") so a non-dns endpoint like minio:9000 works
        self.config = AioConfig(s3={"addressing_style": "path"})

    def _client(self):
        return self.session.client(
            "s3",
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name=self.region,
            config=self.config,
        )

    async def save(self, key: str, data: bytes) -> str:
        content_type = mimetypes.guess_type(key)[0] or "application/octet-stream"
        async with self._client() as client:
            await client.put_object(
                Bucket=self.bucket, Key=key, Body=data, ContentType=content_type
            )
        return key

    async def read(self, key: str) -> bytes:
        async with self._client() as client:
            response = await client.get_object(Bucket=self.bucket, Key=key)
            async with response["Body"] as stream:
                return await stream.read()

    async def delete(self, key: str) -> None:
        async with self._client() as client:
            await client.delete_object(Bucket=self.bucket, Key=key)

    async def exists(self, key: str) -> bool:
        async with self._client() as client:
            try:
                await client.head_object(Bucket=self.bucket, Key=key)
            except ClientError:
                return False
        return True

    def public_url(self, key: str) -> str:
        return f"{self.base_url}/{key}"


def build_storage(settings: Settings) -> Storage:
    if settings.storage_backend == "s3":
        return S3Storage(settings)
    return LocalStorage(settings)
