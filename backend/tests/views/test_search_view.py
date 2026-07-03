from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

from src.schemas.search import SearchResultResponse
from src.views.search_view import SearchView


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


async def test_search_maps_hits_to_responses_with_score():
    search_service = MagicMock()
    search_service.search = AsyncMock(return_value=[(_post(), "b", 0.25)])
    view = SearchView(search_service=search_service)

    results = await view.search("cat", None, 20)

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
    view = SearchView(search_service=search_service)

    assert await view.search("nothing", "b", 5) == []
