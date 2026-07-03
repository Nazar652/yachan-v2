from pydantic import BaseModel

from src.models.attachment import MediaType, ModerationStatus


class AttachmentResponse(BaseModel):
    id: int
    media_type: MediaType
    original_name: str
    # url/thumbnail are null when the attachment is hidden by moderation
    url: str | None = None
    thumbnail_url: str | None = None
    mime_type: str
    width: int | None = None
    height: int | None = None
    duration_seconds: float | None = None
    size_bytes: int | None = None
    moderation_status: ModerationStatus
