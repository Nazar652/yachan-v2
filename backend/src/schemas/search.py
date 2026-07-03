from datetime import datetime

from pydantic import BaseModel


class SearchResultResponse(BaseModel):
    board_slug: str
    thread_id: int
    post_number: int
    is_op: bool
    name: str
    body: str | None
    body_html: str | None
    created_at: datetime
    score: float
