from kink import inject

from src.core.storage import LocalStorage
from src.models.attachment import Attachment
from src.schemas.attachment import AttachmentResponse
from src.services.file_service import FileService
from src.services.post_service import PostService
from src.tasks.attachments import process_attachment


@inject
class AttachmentsView:
    def __init__(
        self,
        file_service: FileService,
        post_service: PostService,
        storage: LocalStorage,
    ) -> None:
        self.file_service = file_service
        self.post_service = post_service
        self.storage = storage

    async def add_attachment(
        self,
        board_slug: str,
        post_number: int,
        filename: str,
        content: bytes,
        content_type: str,
    ) -> AttachmentResponse:
        post = await self.post_service.get_post(board_slug, post_number)
        attachment = await self.file_service.store_attachment(
            post.id, filename, content, content_type
        )
        # thumbnail and dimensions are filled asynchronously by the worker
        process_attachment.delay(attachment.id)  # type: ignore[attr-defined]  celery task
        return self._to_response(attachment)

    def _to_response(self, attachment: Attachment) -> AttachmentResponse:
        thumbnail_url = (
            self.storage.public_url(attachment.thumbnail_path)
            if attachment.thumbnail_path
            else None
        )
        return AttachmentResponse(
            id=attachment.id,
            media_type=attachment.media_type,
            original_name=attachment.original_name,
            url=self.storage.public_url(attachment.file_path),
            thumbnail_url=thumbnail_url,
            mime_type=attachment.mime_type,
            width=attachment.width,
            height=attachment.height,
            duration_seconds=attachment.duration_seconds,
            size_bytes=attachment.size_bytes,
        )
