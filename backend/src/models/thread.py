from datetime import datetime, UTC
from typing import TYPE_CHECKING, ClassVar

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from src.models.board import Board
    from src.models.mediafile import MediaFile
    from src.models.post import Post
    from src.models.user import User


class Thread(SQLModel, table=True):
    __tablename__: ClassVar[str] = "thread"

    id: int | None = Field(default=None, primary_key=True)
    board_id: int = Field(foreign_key="boards.id", nullable=False, index=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    title: str | None = Field(default=None, max_length=150)
    is_locked: bool = Field(default=False, nullable=False)
    is_pinned: bool = Field(default=False, nullable=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC), nullable=False)

    board: Board = Relationship(back_populates="threads")
    author: User | None = Relationship(back_populates="threads")
    posts: list[Post] = Relationship(back_populates="thread")

    @staticmethod
    def ensure_op_has_image(media_files: list[MediaFile]) -> None:
        from src.models.mediafile import MediaType

        if not any(media.media_type in {MediaType.IMAGE, MediaType.GIF} for media in media_files):
            raise ValueError("Thread starter post requires an image or gif attachment")
