from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

from src.services.stats_service import StatsService


def build():
    board_repo = MagicMock()
    board_repo.list_all = AsyncMock(
        return_value=[SimpleNamespace(id=1, slug="b"), SimpleNamespace(id=2, slug="g")]
    )
    thread_repo = MagicMock()
    thread_repo.count_by_board = AsyncMock(return_value={1: 4})
    post_repo = MagicMock()
    post_repo.count_by_board = AsyncMock(return_value={1: 10, 2: 3})
    online_tracker = MagicMock()
    online_tracker.count_by_board = AsyncMock(return_value={"b": 2, "g": 0})
    online_tracker.count_site = AsyncMock(return_value=5)
    service = StatsService(
        board_repo=board_repo,
        thread_repo=thread_repo,
        post_repo=post_repo,
        online_tracker=online_tracker,
    )
    return service, SimpleNamespace(
        board_repo=board_repo,
        thread_repo=thread_repo,
        post_repo=post_repo,
        online_tracker=online_tracker,
    )


async def test_get_site_stats_aggregates_all_sources():
    service, mocks = build()

    stats = await service.get_site_stats()

    assert [board.slug for board in stats.boards] == ["b", "g"]
    assert stats.thread_counts == {1: 4}
    assert stats.post_counts == {1: 10, 2: 3}
    assert stats.online_counts == {"b": 2, "g": 0}
    assert stats.online_total == 5
    mocks.online_tracker.count_by_board.assert_awaited_once_with(["b", "g"])
    mocks.online_tracker.count_site.assert_awaited_once()
