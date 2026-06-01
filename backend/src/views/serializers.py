from src.core.storage import LocalStorage
from src.models.attachment import Attachment
from src.models.post import Post
from src.schemas.attachment import AttachmentResponse
from src.schemas.post import PostResponse


def attachment_response(attachment: Attachment, storage: LocalStorage) -> AttachmentResponse:
    thumbnail_url = (
        storage.public_url(attachment.thumbnail_path) if attachment.thumbnail_path else None
    )
    return AttachmentResponse(
        id=attachment.id,
        media_type=attachment.media_type,
        original_name=attachment.original_name,
        url=storage.public_url(attachment.file_path),
        thumbnail_url=thumbnail_url,
        mime_type=attachment.mime_type,
        width=attachment.width,
        height=attachment.height,
        duration_seconds=attachment.duration_seconds,
        size_bytes=attachment.size_bytes,
    )


def post_response(
    post: Post, attachments: list[Attachment], storage: LocalStorage
) -> PostResponse:
    response = PostResponse.model_validate(post)
    response.attachments = [attachment_response(item, storage) for item in attachments]
    return response
