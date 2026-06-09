from datetime import datetime
from typing import ClassVar

from sqlmodel import Field

from src.models.timestamp_mixin import TimestampMixin
from src.utils.clock import utcnow
from src.utils.types import TZDateTime


class Thread(TimestampMixin, table=True):
    __tablename__: ClassVar[str] = "thread"

    id: int = Field(default=None, primary_key=True)
    board_id: int = Field(foreign_key="board.id", index=True)
    title: str | None = Field(default=None, max_length=150)
    is_locked: bool = Field(default=False)
    is_sticky: bool = Field(default=False)
    reply_count: int = Field(default=0)
    bump_at: datetime = Field(default_factory=utcnow, index=True, sa_type=TZDateTime)
