from typing import ClassVar

from sqlmodel import Field

from src.models.timestamps import TimestampMixin


class Board(TimestampMixin, table=True):
    __tablename__: ClassVar[str] = "board"

    id: int = Field(default=None, primary_key=True)
    slug: str = Field(index=True, unique=True, max_length=20)
    title: str = Field(max_length=100)
    description: str | None = Field(default=None, max_length=500)
    bump_limit: int = Field(default=300)
    is_active: bool = Field(default=True)
    # display order in board listings; lower comes first (admin reorders via drag)
    position: int = Field(default=0, index=True)
