import hashlib
import io

import anyio.to_thread
from kink import inject
from PIL import Image, ImageOps

from src.core.exceptions import FileTooLargeError, UnsupportedMediaTypeError
from src.core.storage import Storage
from src.models.attachment import Attachment, MediaType
from src.repositories.attachment_repo import AttachmentRepository

MAX_UPLOAD_BYTES = 25 * 1024 * 1024
THUMBNAIL_SIZE = (250, 250)

_EXTENSIONS: dict[str, tuple[MediaType, str]] = {
    "image/jpeg": (MediaType.IMAGE, ".jpg"),
    "image/png": (MediaType.IMAGE, ".png"),
    "image/webp": (MediaType.IMAGE, ".webp"),
    "image/gif": (MediaType.GIF, ".gif"),
    "video/webm": (MediaType.VIDEO, ".webm"),
    "video/mp4": (MediaType.VIDEO, ".mp4"),
}


class FileService:
    @inject
    def __init__(self, attachment_repo: AttachmentRepository, storage: Storage) -> None:
        self.attachment_repo = attachment_repo
        self.storage = storage

    async def store_attachment(
        self, post_id: int, filename: str, content: bytes, content_type: str
    ) -> Attachment:
        media_type, extension = self._classify(content_type)
        if len(content) > MAX_UPLOAD_BYTES:
            raise FileTooLargeError(filename)

        # usedforsecurity=False: md5 is only a content fingerprint for dedup.
        # hashing up to 25 MiB is cpu-bound, so run it off the event loop
        md5 = await anyio.to_thread.run_sync(self._md5, content)
        existing = await self.attachment_repo.get_by_md5(md5)
        # identical bytes are stored once and reused across posts
        key = existing.file_path if existing is not None else f"{md5}{extension}"
        if existing is None:
            await self.storage.save(key, content)

        return await self.attachment_repo.create(
            Attachment(
                post_id=post_id,
                media_type=media_type,
                original_name=filename,
                file_path=key,
                mime_type=content_type,
                md5=md5,
                size_bytes=len(content),
            )
        )

    async def process_attachment(self, attachment_id: int) -> None:
        attachment = await self.attachment_repo.get_by_id(attachment_id)
        if attachment is None or attachment.media_type not in (MediaType.IMAGE, MediaType.GIF):
            return

        data = await self.storage.read(attachment.file_path)
        with Image.open(io.BytesIO(data)) as image:
            # bake the exif orientation into the pixels so the thumbnail (which
            # drops exif) is not displayed sideways, and dimensions match display
            oriented = ImageOps.exif_transpose(image)
            width, height = oriented.size
            oriented.thumbnail(THUMBNAIL_SIZE)
            buffer = io.BytesIO()
            oriented.convert("RGB").save(buffer, format="JPEG")

        thumbnail_key = f"thumb/{attachment.md5}.jpg"
        await self.storage.save(thumbnail_key, buffer.getvalue())
        await self.attachment_repo.set_media_info(
            attachment_id,
            thumbnail_path=thumbnail_key,
            width=width,
            height=height,
            duration_seconds=None,
        )

    @staticmethod
    def _md5(content: bytes) -> str:
        return hashlib.md5(content, usedforsecurity=False).hexdigest()

    @staticmethod
    def media_type_for(content_type: str) -> MediaType:
        return FileService._classify(content_type)[0]

    @staticmethod
    def _classify(content_type: str) -> tuple[MediaType, str]:
        if content_type not in _EXTENSIONS:
            raise UnsupportedMediaTypeError(content_type)
        return _EXTENSIONS[content_type]
