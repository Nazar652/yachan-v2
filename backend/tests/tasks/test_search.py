from unittest.mock import AsyncMock, MagicMock

from kink import di

from src.services.search_service import SearchService
from src.tasks.search import embed_post


def test_embed_post_delegates_to_service(monkeypatch):
    instance = MagicMock()
    instance.index_post = AsyncMock()
    monkeypatch.setitem(di.factories, SearchService, lambda container: instance)

    embed_post(10)

    instance.index_post.assert_awaited_once_with(10)
