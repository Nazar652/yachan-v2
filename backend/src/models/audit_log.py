from datetime import datetime
from typing import Any, ClassVar

from sqlalchemy import BigInteger, Column
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel

from src.utils.clock import utcnow


class AuditLog(SQLModel, table=True):
    __tablename__: ClassVar[str] = "audit_log"

    # rows are written by the audit_log_changes() db trigger, not the orm; this
    # model exists so alembic manages the table and the app can read the trail.
    id: int = Field(default=None, primary_key=True)
    table_name: str = Field(index=True, max_length=63)
    op: str = Field(max_length=10)  # INSERT / UPDATE / DELETE
    row_data: dict[str, Any] | None = Field(default=None, sa_column=Column(JSONB))
    old_data: dict[str, Any] | None = Field(default=None, sa_column=Column(JSONB))  # set on UPDATE
    txid: int = Field(sa_column=Column(BigInteger, nullable=False))
    at: datetime = Field(default_factory=utcnow)
