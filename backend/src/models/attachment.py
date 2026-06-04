from enum import StrEnum
from typing import ClassVar

from sqlmodel import Field

from src.models.timestamp_mixin import TimestampMixin


class MediaType(StrEnum):
    IMAGE = "image"
    VIDEO = "video"
    GIF = "gif"


class Attachment(TimestampMixin, table=True):
    __tablename__: ClassVar[str] = "attachment"

    id: int = Field(default=None, primary_key=True)
    post_id: int = Field(foreign_key="post.id", index=True)
    media_type: MediaType
    original_name: str = Field(max_length=255)
    # storage-agnostic locator, resolved by FileService (local path now, object key later)
    file_path: str = Field(max_length=500)
    thumbnail_path: str | None = Field(default=None, max_length=500)
    mime_type: str = Field(max_length=100)
    md5: str = Field(index=True, max_length=32)  # used for dedup
    size_bytes: int | None = Field(default=None)
    width: int | None = Field(default=None)
    height: int | None = Field(default=None)
    duration_seconds: float | None = Field(default=None)
