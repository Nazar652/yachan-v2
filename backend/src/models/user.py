from datetime import datetime, UTC
from typing import TYPE_CHECKING, ClassVar

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from src.models.post import Post
    from src.models.thread import Thread


class User(SQLModel, table=True):
    __tablename__: ClassVar[str] = "user"

    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True, max_length=50)
    display_name: str | None = Field(default=None, max_length=100)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC), nullable=False)

    threads: list[Thread] = Relationship(back_populates="author")
    posts: list[Post] = Relationship(back_populates="author")
