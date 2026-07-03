from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from src.schemas.post import PostResponse


class ThreadCreate(BaseModel):
    title: str | None = Field(default=None, max_length=150)
    name: str | None = Field(default=None, max_length=100)
    body: str | None = Field(default=None, max_length=5000)
    sage: bool = False


class ImagePreview(BaseModel):
    url: str
    thumbnail_url: str
    width: int | None = None
    height: int | None = None


class OpPostPreview(BaseModel):
    body: str | None
    body_html: str | None
    thumbnail_url: str | None
    width: int | None = None
    height: int | None = None
    images: list[ImagePreview] = Field(default_factory=list)


class ReplyPreview(BaseModel):
    id: int
    post_number: int
    name: str | None
    body: str | None
    body_html: str | None
    created_at: datetime


class ThreadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    board_id: int
    title: str | None
    is_locked: bool
    is_sticky: bool
    reply_count: int
    bump_at: datetime
    created_at: datetime
    op_post: OpPostPreview | None = None
    last_replies: list[ReplyPreview] = Field(default_factory=list)


class ThreadDetailResponse(ThreadResponse):
    summary: str | None = None
    summary_updated_at: datetime | None = None
    posts: list[PostResponse] = Field(default_factory=list)


class LatestThreadResponse(BaseModel):
    # cross-board "latest activity" strip on the home page
    id: int
    board_slug: str
    title: str | None
    reply_count: int
    bump_at: datetime
    created_at: datetime
    thumbnail_url: str | None = None
    last_reply: ReplyPreview | None = None
