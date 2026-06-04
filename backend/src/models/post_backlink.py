from typing import ClassVar

from sqlalchemy import UniqueConstraint
from sqlmodel import Field

from src.models.timestamp_mixin import TimestampMixin


class PostBacklink(TimestampMixin, table=True):
    __tablename__: ClassVar[str] = "post_backlink"
    __table_args__: ClassVar = (
        UniqueConstraint("source_post_id", "target_post_id", name="uq_backlink_pair"),
    )

    id: int = Field(default=None, primary_key=True)
    source_post_id: int = Field(foreign_key="post.id", index=True)  # post that contains the link
    target_post_id: int = Field(foreign_key="post.id", index=True)  # post being referenced
