from datetime import datetime
from typing import ClassVar

from sqlalchemy import UniqueConstraint
from sqlmodel import Field

from src.models.timestamp_mixin import TimestampMixin


class Post(TimestampMixin, table=True):
    __tablename__: ClassVar[str] = "post"
    __table_args__: ClassVar = (
        UniqueConstraint("board_id", "post_number", name="uq_post_board_number"),
    )

    id: int = Field(default=None, primary_key=True)
    post_number: int  # per-board counter, unique within a board
    thread_id: int = Field(foreign_key="thread.id", index=True)
    board_id: int = Field(foreign_key="board.id", index=True)
    name: str = Field(default="Anonymous", max_length=100)
    tripcode: str | None = Field(default=None, max_length=50)
    body: str | None = Field(default=None, max_length=5000)  # raw markdown
    body_html: str | None = Field(default=None)  # rendered html sent to clients
    sage: bool = Field(default=False)
    is_op: bool = Field(default=False)
    is_edited: bool = Field(default=False)
    edited_at: datetime | None = Field(default=None)
    ip_hash: str = Field(max_length=64)  # never exposed in the api
    deleted: bool = Field(default=False)
    deleted_by: int | None = Field(default=None, foreign_key="mod_account.id")
