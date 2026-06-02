from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class BoardCreate(BaseModel):
    slug: str = Field(pattern=r"^[a-z0-9_]{1,20}$")
    title: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    bump_limit: int = Field(default=300, gt=0)


class BoardUpdate(BaseModel):
    # partial update; slug is immutable (it backs the per-board post sequence).
    # only fields explicitly provided are applied (model_dump(exclude_unset=True)).
    title: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    bump_limit: int | None = Field(default=None, gt=0)
    is_active: bool | None = None


class BoardResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    title: str
    description: str | None
    bump_limit: int
    is_active: bool
    created_at: datetime
