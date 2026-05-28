from datetime import UTC, datetime
from typing import ClassVar

from sqlmodel import Field, SQLModel


class Board(SQLModel, table=True):
    __tablename__: ClassVar[str] = "board"

    id: int | None = Field(default=None, primary_key=True)
    slug: str = Field(index=True, unique=True, max_length=20)
    title: str = Field(max_length=100)
    description: str | None = Field(default=None, max_length=500)
    bump_limit: int = Field(default=300)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
