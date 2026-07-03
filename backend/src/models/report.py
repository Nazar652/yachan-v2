from typing import ClassVar

from sqlmodel import Field

from src.models.timestamp_mixin import TimestampMixin


class Report(TimestampMixin, table=True):
    __tablename__: ClassVar[str] = "report"

    id: int = Field(default=None, primary_key=True)
    post_id: int = Field(foreign_key="post.id", index=True)
    board_id: int | None = Field(default=None, foreign_key="board.id")
    reason: str | None = Field(default=None, max_length=500)
    ip_hash: str = Field(max_length=64)
    is_auto: bool = Field(default=False)  # raised by text moderation, not a human
    is_resolved: bool = Field(default=False)
    resolved_by: int | None = Field(default=None, foreign_key="mod_account.id")
