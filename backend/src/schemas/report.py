from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ReportCreate(BaseModel):
    reason: str | None = Field(default=None, max_length=500)


class ReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    post_id: int
    board_id: int | None
    board_slug: str
    thread_id: int
    post_number: int
    reason: str | None
    is_auto: bool
    is_resolved: bool
    created_at: datetime
