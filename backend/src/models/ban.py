from datetime import datetime
from typing import ClassVar

from sqlmodel import Field, SQLModel

from src.core.clock import utcnow


class Ban(SQLModel, table=True):
    __tablename__: ClassVar[str] = "ban"

    id: int | None = Field(default=None, primary_key=True)
    ip_hash: str = Field(index=True, max_length=64)
    board_id: int | None = Field(default=None, foreign_key="board.id")  # null = global ban
    reason: str | None = Field(default=None, max_length=500)
    created_by: int | None = Field(default=None, foreign_key="mod_account.id")
    expires_at: datetime | None = Field(default=None)  # null = permanent
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=utcnow)
