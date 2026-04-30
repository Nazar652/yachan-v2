from datetime import datetime, UTC
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from src.models.thread import Thread


class Board(SQLModel, table=True):
    __tablename__ = "board"

    id: int | None = Field(default=None, primary_key=True)
    code: str = Field(index=True, unique=True, max_length=20)
    title: str = Field(max_length=100)
    description: str | None = Field(default=None, max_length=500)
    is_active: bool = Field(default=True, nullable=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC), nullable=False)

    threads: list[Thread] = Relationship(back_populates="board")

