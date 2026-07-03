from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.core.exceptions import NotFoundError
from src.services.search_service import SearchService


def build():
    post_repo = MagicMock()
    post_embedding_repo = MagicMock()
    post_embedding_repo.upsert = AsyncMock()
    post_embedding_repo.search = AsyncMock(return_value=[])
    board_repo = MagicMock()
    board_repo.get_by_slug = AsyncMock(return_value=SimpleNamespace(id=3))
    embedding_model = MagicMock()
    service = SearchService(
        post_repo=post_repo,
        post_embedding_repo=post_embedding_repo,
        board_repo=board_repo,
        embedding_model=embedding_model,
    )
    return service, post_repo, post_embedding_repo, board_repo, embedding_model


async def test_index_post_embeds_and_upserts():
    service, post_repo, post_embedding_repo, _board_repo, model = build()
    post_repo.get_by_id = AsyncMock(return_value=SimpleNamespace(id=10, body="hello world"))
    model.embed = MagicMock(return_value=[0.1, 0.2, 0.3])

    await service.index_post(10)

    model.embed.assert_called_once_with("hello world")
    post_embedding_repo.upsert.assert_awaited_once_with(10, [0.1, 0.2, 0.3])


async def test_index_post_skips_missing_post():
    service, post_repo, post_embedding_repo, _board_repo, model = build()
    post_repo.get_by_id = AsyncMock(return_value=None)
    model.embed = MagicMock()

    await service.index_post(10)

    model.embed.assert_not_called()
    post_embedding_repo.upsert.assert_not_awaited()


async def test_index_post_skips_empty_body():
    service, post_repo, post_embedding_repo, _board_repo, model = build()
    post_repo.get_by_id = AsyncMock(return_value=SimpleNamespace(id=10, body=""))
    model.embed = MagicMock()

    await service.index_post(10)

    model.embed.assert_not_called()
    post_embedding_repo.upsert.assert_not_awaited()


async def test_index_all_embeds_every_post_with_body():
    service, post_repo, post_embedding_repo, _board_repo, model = build()
    post_repo.list_with_body = AsyncMock(
        return_value=[SimpleNamespace(id=1, body="a"), SimpleNamespace(id=2, body="bb")]
    )
    model.embed = MagicMock(side_effect=lambda text: [float(len(text))])

    count = await service.index_all()

    assert count == 2
    assert post_embedding_repo.upsert.await_count == 2
    post_embedding_repo.upsert.assert_any_await(1, [1.0])
    post_embedding_repo.upsert.assert_any_await(2, [2.0])


async def test_search_embeds_query_and_searches_all_boards():
    service, _post_repo, post_embedding_repo, board_repo, model = build()
    model.embed = MagicMock(return_value=[0.1, 0.2])
    hits = [(SimpleNamespace(id=5), "b", 0.1)]
    post_embedding_repo.search = AsyncMock(return_value=hits)

    result = await service.search("cats", limit=7)

    assert result == hits
    board_repo.get_by_slug.assert_not_awaited()
    model.embed.assert_called_once_with("cats")
    post_embedding_repo.search.assert_awaited_once_with([0.1, 0.2], "cats", board_id=None, limit=7)


async def test_search_scopes_to_board_when_slug_given():
    service, _post_repo, post_embedding_repo, board_repo, model = build()
    board_repo.get_by_slug = AsyncMock(return_value=SimpleNamespace(id=3))
    model.embed = MagicMock(return_value=[0.5])

    await service.search("cats", board_slug="g")

    board_repo.get_by_slug.assert_awaited_once_with("g")
    post_embedding_repo.search.assert_awaited_once_with([0.5], "cats", board_id=3, limit=20)


async def test_search_unknown_board_raises_not_found():
    service, _post_repo, _post_embedding_repo, board_repo, model = build()
    board_repo.get_by_slug = AsyncMock(return_value=None)
    model.embed = MagicMock()

    with pytest.raises(NotFoundError):
        await service.search("cats", board_slug="missing")
    model.embed.assert_not_called()
