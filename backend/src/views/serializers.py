from src.core.storage import Storage
from src.models.attachment import Attachment, ModerationStatus
from src.models.post import Post
from src.schemas.attachment import AttachmentResponse
from src.schemas.post import PostResponse


def is_media_hidden(status: ModerationStatus, board_is_nsfw: bool) -> bool:
    # blocked is hidden everywhere; flagged (sexual) is hidden unless the board is 18+
    if status == ModerationStatus.BLOCKED:
        return True
    return status == ModerationStatus.FLAGGED and not board_is_nsfw


def attachment_response(
    attachment: Attachment, storage: Storage, board_is_nsfw: bool
) -> AttachmentResponse:
    hidden = is_media_hidden(attachment.moderation_status, board_is_nsfw)
    thumbnail_url = (
        storage.public_url(attachment.thumbnail_path)
        if attachment.thumbnail_path and not hidden
        else None
    )

    return AttachmentResponse(
        id=attachment.id,
        media_type=attachment.media_type,
        original_name=attachment.original_name,
        url=None if hidden else storage.public_url(attachment.file_path),
        thumbnail_url=thumbnail_url,
        mime_type=attachment.mime_type,
        width=attachment.width,
        height=attachment.height,
        duration_seconds=attachment.duration_seconds,
        size_bytes=attachment.size_bytes,
        moderation_status=attachment.moderation_status,
    )


def post_response(
    post: Post, attachments: list[Attachment], storage: Storage, board_is_nsfw: bool
) -> PostResponse:
    response = PostResponse.model_validate(post)

    response.attachments = [
        attachment_response(item, storage, board_is_nsfw) for item in attachments
    ]

    return response
