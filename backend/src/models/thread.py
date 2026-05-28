from datetime import UTC, datetime
from typing import ClassVar

from sqlmodel import Field, SQLModel


class Thread(SQLModel, table=True):
    __tablename__: ClassVar[str] = "thread"

    id: int | None = Field(default=None, primary_key=True)
    board_id: int = Field(foreign_key="board.id", index=True)
    title: str | None = Field(default=None, max_length=150)
    is_locked: bool = Field(default=False)
    is_sticky: bool = Field(default=False)
    reply_count: int = Field(default=0)
    bump_at: datetime = Field(default_factory=lambda: datetime.now(UTC), index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
