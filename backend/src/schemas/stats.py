from pydantic import BaseModel


class BoardStatsResponse(BaseModel):
    slug: str
    thread_count: int
    post_count: int
    online_count: int


class SiteStatsResponse(BaseModel):
    board_count: int
    thread_count: int
    post_count: int
    online_count: int
    boards: list[BoardStatsResponse]
