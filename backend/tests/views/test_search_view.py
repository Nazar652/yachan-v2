from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from src.core.exceptions import RateLimitedError
from src.models.attachment import ModerationStatus
from src.schemas.search import SearchResultResponse, SimilarThreadResponse
from src.views.search_view import SearchView
from tests.views._factories import request_ns, settings_ns


def _post():
    return SimpleNamespace(
        thread_id=5,
        post_number=42,
        is_op=True,
        name="Anon",
        body="a cat",
        body_html="<p>a cat</p>",
        created_at=datetime(2026, 1, 1),
    )


def _view(search_service=None, board_service=None, storage=None, allowed=True):
    rate_limiter = MagicMock()
    rate_limiter.is_allowed = AsyncMock(return_value=allowed)
    return SearchView(
        search_service=search_service or MagicMock(),
        board_service=board_service or MagicMock(),
        storage=storage or MagicMock(),
        rate_limiter=rate_limiter,
        settings=settings_ns(),
    )


async def test_search_maps_hits_to_responses_with_score():
    search_service = MagicMock()
    search_service.search = AsyncMock(return_value=[(_post(), "b", 0.25)])
    view = _view(search_service=search_service)

    results = await view.search("cat", None, 20, request_ns())

    assert len(results) == 1
    result = results[0]
    assert isinstance(result, SearchResultResponse)
    assert result.board_slug == "b"
    assert result.thread_id == 5
    assert result.post_number == 42
    assert result.is_op is True
    assert result.score == 0.75
    search_service.search.assert_awaited_once_with("cat", board_slug=None, limit=20)


async def test_search_empty_when_no_hits():
    search_service = MagicMock()
    search_service.search = AsyncMock(return_value=[])
    view = _view(search_service=search_service)

    assert await view.search("nothing", "b", 5, request_ns()) == []


def _board(slug: str, is_nsfw: bool = False):
    return SimpleNamespace(slug=slug, is_nsfw=is_nsfw)


def _thread(thread_id: int, title: str | None, reply_count: int = 3):
    return SimpleNamespace(id=thread_id, title=title, reply_count=reply_count)


def _op_post(body: str | None):
    return SimpleNamespace(body=body)


def _image(moderation_status=ModerationStatus.SAFE):
    return SimpleNamespace(
        moderation_status=moderation_status,
        thumbnail_path="thumb.jpg",
        file_path="full.jpg",
    )


async def test_similar_threads_maps_matches_with_thumbnail_and_snippet():
    search_service = MagicMock()
    thread = _thread(9, "a long thread title")
    op_post = _op_post("x" * 150)
    search_service.similar_threads = AsyncMock(
        return_value=[(thread, "b", op_post, [_image()], 0.2)]
    )
    board_service = MagicMock()
    board_service.list_boards = AsyncMock(return_value=[_board("b")])
    storage = MagicMock()
    storage.public_url = MagicMock(return_value="https://cdn/thumb.jpg")
    view = _view(search_service=search_service, board_service=board_service, storage=storage)

    results = await view.similar_threads("b", 7, request_ns())

    assert len(results) == 1
    result = results[0]
    assert isinstance(result, SimilarThreadResponse)
    assert result.board_slug == "b"
    assert result.thread_id == 9
    assert result.title == "a long thread title"
    assert result.op_snippet == "x" * 120 + "…"
    assert result.thumbnail_url == "https://cdn/thumb.jpg"
    assert result.reply_count == 3
    assert result.score == 0.8
    search_service.similar_threads.assert_awaited_once_with("b", 7)


async def test_similar_threads_hides_blocked_image_thumbnail():
    search_service = MagicMock()
    thread = _thread(9, None)
    op_post = _op_post(None)
    search_service.similar_threads = AsyncMock(
        return_value=[(thread, "b", op_post, [_image(ModerationStatus.BLOCKED)], 0.1)]
    )
    board_service = MagicMock()
    board_service.list_boards = AsyncMock(return_value=[_board("b")])
    view = _view(search_service=search_service, board_service=board_service)

    results = await view.similar_threads("b", 7, request_ns())

    assert results[0].thumbnail_url is None
    assert results[0].op_snippet is None


async def test_similar_threads_empty_when_no_matches():
    search_service = MagicMock()
    search_service.similar_threads = AsyncMock(return_value=[])
    board_service = MagicMock()
    board_service.list_boards = AsyncMock(return_value=[])
    view = _view(search_service=search_service, board_service=board_service)

    assert await view.similar_threads("b", 7, request_ns()) == []


async def test_similar_threads_for_text_delegates_to_service():
    search_service = MagicMock()
    thread = _thread(9, "title")
    op_post = _op_post("short body")
    search_service.similar_threads_for_text = AsyncMock(
        return_value=[(thread, "b", op_post, [], 0.05)]
    )
    board_service = MagicMock()
    board_service.list_boards = AsyncMock(return_value=[_board("b")])
    view = _view(search_service=search_service, board_service=board_service)

    results = await view.similar_threads_for_text("b", "duplicate text", request_ns())

    assert len(results) == 1
    assert results[0].score == 0.95
    search_service.similar_threads_for_text.assert_awaited_once_with("b", "duplicate text")


async def test_search_rate_limited():
    view = _view(allowed=False)
    with pytest.raises(RateLimitedError):
        await view.search("cat", None, 20, request_ns())
