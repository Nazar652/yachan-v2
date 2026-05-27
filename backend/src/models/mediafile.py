from datetime import datetime, UTC
from enum import StrEnum
from typing import TYPE_CHECKING, ClassVar

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from src.models.post import Post


class MediaType(StrEnum):
    IMAGE = "image"
    VIDEO = "video"
    GIF = "gif"


class MediaFile(SQLModel, table=True):
    __tablename__: ClassVar[str] = "media_file"

    id: int | None = Field(default=None, primary_key=True)
    post_id: int = Field(foreign_key="posts.id", nullable=False, index=True)
    media_type: MediaType = Field(nullable=False)
    file_url: str = Field(nullable=False, max_length=500)
    thumbnail_url: str | None = Field(default=None, max_length=500)
    width: int | None = Field(default=None)
    height: int | None = Field(default=None)
    duration_seconds: float | None = Field(default=None)
    size_bytes: int | None = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC), nullable=False)

    post: Post = Relationship(back_populates="media_files")

