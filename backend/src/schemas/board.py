from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


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

    @model_validator(mode="before")
    @classmethod
    def reject_null_on_required(cls, data: Any) -> Any:
        # description is the only nullable board column; an explicit null on a
        # required field is meaningless (omit the field to leave it unchanged),
        # and applying it would blow up on flush against a NOT NULL column.
        if isinstance(data, dict):
            for field in ("title", "bump_limit", "is_active"):
                if field in data and data[field] is None:
                    raise ValueError(f"{field} may not be null")
        return data


class BoardReorder(BaseModel):
    # the complete set of board slugs in the desired display order; the service
    # rejects anything that is not a permutation of all existing boards
    slugs: list[str] = Field(min_length=1)


class BoardResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    title: str
    description: str | None
    bump_limit: int
    is_active: bool
    position: int
    created_at: datetime
