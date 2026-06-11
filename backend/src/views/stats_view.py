from kink import inject
from starlette.requests import Request

from src.core.config import Settings
from src.schemas.stats import BoardStatsResponse, SiteStatsResponse
from src.services.stats_service import StatsService
from src.utils.online import OnlineTracker
from src.views.dependencies import client_ip_hash


class StatsView:
    @inject
    def __init__(
        self,
        stats_service: StatsService,
        online_tracker: OnlineTracker,
        settings: Settings,
    ) -> None:
        self.stats_service = stats_service
        self.online_tracker = online_tracker
        self.settings = settings

    async def get_site_stats(self, request: Request) -> SiteStatsResponse:
        # the requester is online too, so count them before reading
        await self.online_tracker.touch(client_ip_hash(request, self.settings))
        stats = await self.stats_service.get_site_stats()

        boards = [
            BoardStatsResponse(
                slug=board.slug,
                thread_count=stats.thread_counts.get(board.id, 0),
                post_count=stats.post_counts.get(board.id, 0),
                online_count=stats.online_counts.get(board.slug, 0),
            )
            for board in stats.boards
        ]
        return SiteStatsResponse(
            board_count=len(boards),
            thread_count=sum(stats.thread_counts.values()),
            post_count=sum(stats.post_counts.values()),
            online_count=stats.online_total,
            boards=boards,
        )
