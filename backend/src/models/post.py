from datetime import datetime, UTC
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from src.models.mediafile import MediaFile
    from src.models.thread import Thread
    from src.models.user import User


class Post(SQLModel, table=True):
    __tablename__ = "post"

    id: int | None = Field(default=None, primary_key=True)
    thread_id: int = Field(foreign_key="threads.id", nullable=False, index=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    content: str | None = Field(default=None, max_length=5000)
    is_op: bool = Field(default=False, nullable=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC), nullable=False)

    thread: Thread = Relationship(back_populates="posts")
    author: User | None = Relationship(back_populates="posts")
    media_files: list[MediaFile] = Relationship(back_populates="post")
