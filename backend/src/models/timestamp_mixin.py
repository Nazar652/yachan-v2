from datetime import datetime

from sqlmodel import Field, SQLModel

from src.utils.clock import utcnow


class TimestampMixin(SQLModel):
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(
        default_factory=utcnow,
        sa_column_kwargs={"onupdate": utcnow},
    )
