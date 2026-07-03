from types import SimpleNamespace
from unittest.mock import MagicMock

from src.repositories.post_embedding_repo import PostEmbeddingRepository


async def test_upsert_executes_statement(session):
    repo = PostEmbeddingRepository(session=session)

    await repo.upsert(1, [0.1, 0.2, 0.3])

    session.execute.assert_awaited_once()


async def test_search_returns_post_slug_distance_tuples(session):
    post = SimpleNamespace(id=5)
    result = MagicMock()
    result.all.return_value = [(post, "b", 0.12)]
    session.execute.return_value = result
    repo = PostEmbeddingRepository(session=session)

    matches = await repo.search([0.1, 0.2, 0.3], "cats", limit=10)

    assert matches == [(post, "b", 0.12)]
    session.execute.assert_awaited_once()


async def test_search_filters_by_board(session):
    result = MagicMock()
    result.all.return_value = []
    session.execute.return_value = result
    repo = PostEmbeddingRepository(session=session)

    matches = await repo.search([0.1, 0.2, 0.3], "cats", board_id=2)

    assert matches == []
    session.execute.assert_awaited_once()
