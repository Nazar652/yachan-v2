from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from src.schemas.attachment import AttachmentResponse


class PostCreate(BaseModel):
    name: str | None = Field(default=None, max_length=100)
    body: str | None = Field(default=None, max_length=5000)
    sage: bool = False


class PostEditCreate(BaseModel):
    new_body: str | None = Field(default=None, max_length=5000)


class PostResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    post_number: int
    thread_id: int
    board_id: int
    name: str
    tripcode: str | None
    body: str | None
    body_html: str | None
    sage: bool
    is_op: bool
    is_edited: bool
    edited_at: datetime | None
    created_at: datetime
    can_edit: bool = False
    attachments: list[AttachmentResponse] = Field(default_factory=list)


class PostEditResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    post_id: int
    original_body: str | None
    original_body_html: str | None
    edited_at: datetime
