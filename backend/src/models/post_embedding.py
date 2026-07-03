from typing import ClassVar

from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, ForeignKey, Integer
from sqlmodel import Field

from src.models.timestamp_mixin import TimestampMixin

EMBEDDING_DIMENSIONS = 384


class PostEmbedding(TimestampMixin, table=True):
    __tablename__: ClassVar[str] = "post_embedding"

    post_id: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey("post.id", ondelete="CASCADE"),
            primary_key=True,
        )
    )
    embedding: list[float] = Field(
        sa_column=Column(Vector(EMBEDDING_DIMENSIONS), nullable=False)
    )
