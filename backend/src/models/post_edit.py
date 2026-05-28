from datetime import datetime
from typing import ClassVar

from sqlmodel import Field, SQLModel

from src.core.clock import utcnow


class PostEdit(SQLModel, table=True):
    __tablename__: ClassVar[str] = "post_edit"

    id: int | None = Field(default=None, primary_key=True)
    post_id: int = Field(foreign_key="post.id", index=True)
    original_body: str | None = Field(default=None)
    original_body_html: str | None = Field(default=None)
    edited_at: datetime = Field(default_factory=utcnow)
