from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from src.schemas.post import PostResponse


class ThreadCreate(BaseModel):
    title: str | None = Field(default=None, max_length=150)
    # fields of the opening post
    name: str | None = Field(default=None, max_length=100)
    body: str | None = Field(default=None, max_length=5000)
    sage: bool = False


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


class ThreadDetailResponse(ThreadResponse):
    posts: list[PostResponse] = Field(default_factory=list)
