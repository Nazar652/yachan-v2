from dataclasses import dataclass

from fastapi import UploadFile

from src.core.exceptions import TooManyAttachmentsError
from src.models.attachment import Attachment, MediaType
from src.services.file_service import FileService
from src.tasks.attachments import process_attachment

MAX_ATTACHMENTS = 10


@dataclass(frozen=True)
class Upload:
    filename: str
    content: bytes
    content_type: str
    media_type: MediaType


async def read_uploads(files: list[UploadFile]) -> list[Upload]:
    """Read non-empty uploads, validating count and media type up front so a
    bad request is rejected before anything is written."""
    uploads: list[Upload] = []
    for file in files:
        content = await file.read()
        if not file.filename or not content:
            continue
        content_type = file.content_type or ""
        uploads.append(
            Upload(file.filename, content, content_type, FileService.media_type_for(content_type))
        )
    if len(uploads) > MAX_ATTACHMENTS:
        raise TooManyAttachmentsError(f"at most {MAX_ATTACHMENTS} attachments per post")
    return uploads


def contains_image(uploads: list[Upload]) -> bool:
    return any(upload.media_type in (MediaType.IMAGE, MediaType.GIF) for upload in uploads)


async def store_uploads(
    file_service: FileService, post_id: int, uploads: list[Upload]
) -> list[Attachment]:
    stored: list[Attachment] = []
    for upload in uploads:
        attachment = await file_service.store_attachment(
            post_id, upload.filename, upload.content, upload.content_type
        )
        process_attachment.delay(attachment.id)  # type: ignore[attr-defined]  celery task
        stored.append(attachment)
    return stored
