from datetime import datetime
from types import SimpleNamespace

from src.schemas.thread import ThreadCreate, ThreadDetailResponse, ThreadResponse


def test_thread_create_defaults():
    thread = ThreadCreate()
    assert thread.title is None
    assert thread.sage is False


def test_thread_response_from_attributes():
    obj = SimpleNamespace(
        id=1,
        board_id=1,
        title="hello",
        is_locked=False,
        is_sticky=False,
        reply_count=3,
        bump_at=datetime(2026, 1, 1),
        created_at=datetime(2026, 1, 1),
    )
    response = ThreadResponse.model_validate(obj)
    assert response.reply_count == 3


def test_thread_detail_defaults_posts_empty():
    detail = ThreadDetailResponse(
        id=1,
        board_id=1,
        title=None,
        is_locked=False,
        is_sticky=False,
        reply_count=0,
        bump_at=datetime(2026, 1, 1),
        created_at=datetime(2026, 1, 1),
    )
    assert detail.posts == []
