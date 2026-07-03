from dataclasses import dataclass

from fastapi import UploadFile

from src.celery_app import celery
from src.core.config import get_settings
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
    media_base = get_settings().media_internal_url.rstrip("/")

    for upload in uploads:
        attachment = await file_service.store_attachment(
            post_id, upload.filename, upload.content, upload.content_type
        )
        process_attachment.delay(attachment.id)  # type: ignore[attr-defined]
        # absolute, service-reachable url; falls back to the browser public url when
        # media_internal_url is unset (prod, where public_url is already absolute)
        image_url = (
            f"{media_base}/{attachment.file_path}"
            if media_base
            else file_service.storage.public_url(attachment.file_path)
        )
        # fire-and-forget moderation: addressed by string name, consumed by the
        # separate moderation worker off the `moderation` queue (see moderation-contract.md)
        celery.send_task(
            "moderate_image",
            args=[attachment.id, image_url, "nsfw"],
            queue="moderation",
        )
        stored.append(attachment)
    return stored
