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


async def test_get_by_post_id_normalizes_to_plain_floats(session):
    result = MagicMock()
    result.scalar_one_or_none.return_value = [0.1, 0.2, 0.3]
    session.execute.return_value = result
    repo = PostEmbeddingRepository(session=session)

    embedding = await repo.get_by_post_id(5)

    assert embedding == [0.1, 0.2, 0.3]
    session.execute.assert_awaited_once()


async def test_get_by_post_id_returns_none_when_missing(session):
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    session.execute.return_value = result
    repo = PostEmbeddingRepository(session=session)

    embedding = await repo.get_by_post_id(5)

    assert embedding is None


async def test_similar_threads_returns_thread_slug_post_distance_tuples(session):
    thread = SimpleNamespace(id=1)
    post = SimpleNamespace(id=5, thread_id=1)
    result = MagicMock()
    result.all.return_value = [(thread, "b", post, 0.2)]
    session.execute.return_value = result
    repo = PostEmbeddingRepository(session=session)

    matches = await repo.similar_threads([0.1, 0.2, 0.3], exclude_thread_id=99)

    assert matches == [(thread, "b", post, 0.2)]
    session.execute.assert_awaited_once()


async def test_similar_threads_filters_by_board_and_max_distance(session):
    result = MagicMock()
    result.all.return_value = []
    session.execute.return_value = result
    repo = PostEmbeddingRepository(session=session)

    matches = await repo.similar_threads(
        [0.1, 0.2, 0.3], exclude_thread_id=1, board_id=2, max_distance=0.65
    )

    assert matches == []
    session.execute.assert_awaited_once()
