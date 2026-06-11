from unittest.mock import AsyncMock, MagicMock

from src.schemas.stats import SiteStatsResponse
from src.services.stats_service import SiteStats
from src.views.stats_view import StatsView
from tests.views._factories import board_ns, request_ns, settings_ns


def build(stats: SiteStats):
    stats_service = MagicMock()
    stats_service.get_site_stats = AsyncMock(return_value=stats)
    online_tracker = MagicMock()
    online_tracker.touch = AsyncMock()
    view = StatsView(
        stats_service=stats_service,
        online_tracker=online_tracker,
        settings=settings_ns(),
    )
    return view, online_tracker


async def test_get_site_stats_maps_response():
    view, online_tracker = build(
        SiteStats(
            boards=[board_ns(), board_ns(id=2, slug="g")],
            thread_counts={1: 4, 2: 2},
            post_counts={1: 10},
            online_counts={"b": 3},
            online_total=7,
        )
    )

    result = await view.get_site_stats(request_ns())

    assert isinstance(result, SiteStatsResponse)
    assert result.board_count == 2
    assert result.thread_count == 6
    assert result.post_count == 10
    assert result.online_count == 7
    assert result.boards[0].slug == "b"
    assert result.boards[0].thread_count == 4
    assert result.boards[0].post_count == 10
    assert result.boards[0].online_count == 3
    # boards missing from the count maps fall back to zero
    assert result.boards[1].post_count == 0
    assert result.boards[1].online_count == 0


async def test_get_site_stats_touches_site_presence():
    view, online_tracker = build(
        SiteStats(boards=[], thread_counts={}, post_counts={}, online_counts={}, online_total=0)
    )

    await view.get_site_stats(request_ns())

    online_tracker.touch.assert_awaited_once()
    assert online_tracker.touch.await_args.args[0]  # a non-empty ip hash
