from datetime import datetime
from typing import ClassVar

from sqlmodel import Field

from src.models.timestamp_mixin import TimestampMixin
from src.utils.clock import utcnow
from src.utils.types import TZDateTime


class PostEdit(TimestampMixin, table=True):
    __tablename__: ClassVar[str] = "post_edit"

    id: int = Field(default=None, primary_key=True)
    post_id: int = Field(foreign_key="post.id", index=True)
    original_body: str | None = Field(default=None)
    original_body_html: str | None = Field(default=None)
    edited_at: datetime = Field(default_factory=utcnow, sa_type=TZDateTime)
