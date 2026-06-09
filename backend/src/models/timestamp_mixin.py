from datetime import datetime

from sqlmodel import Field, SQLModel

from src.utils.types import TZDateTime
from src.utils.clock import utcnow


class TimestampMixin(SQLModel):
    created_at: datetime = Field(
        default_factory=utcnow,
        sa_type=TZDateTime,
    )
    updated_at: datetime = Field(
        default_factory=utcnow,
        sa_type=TZDateTime,
        sa_column_kwargs={"onupdate": utcnow},
    )
