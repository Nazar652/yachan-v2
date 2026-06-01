from pydantic import BaseModel

from src.models.attachment import MediaType


class AttachmentResponse(BaseModel):
    id: int
    media_type: MediaType
    original_name: str
    url: str
    thumbnail_url: str | None = None
    mime_type: str
    width: int | None = None
    height: int | None = None
    duration_seconds: float | None = None
    size_bytes: int | None = None
