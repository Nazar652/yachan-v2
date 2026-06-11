from dataclasses import dataclass

from kink import inject

from src.models.board import Board
from src.repositories.board_repo import BoardRepository
from src.repositories.post_repo import PostRepository
from src.repositories.thread_repo import ThreadRepository
from src.utils.online import OnlineTracker


@dataclass
class SiteStats:
    boards: list[Board]
    thread_counts: dict[int, int]  # board id -> thread count
    post_counts: dict[int, int]  # board id -> post count
    online_counts: dict[str, int]  # board slug -> online count
    online_total: int


class StatsService:
    @inject
    def __init__(
        self,
        board_repo: BoardRepository,
        thread_repo: ThreadRepository,
        post_repo: PostRepository,
        online_tracker: OnlineTracker,
    ) -> None:
        self.board_repo = board_repo
        self.thread_repo = thread_repo
        self.post_repo = post_repo
        self.online_tracker = online_tracker

    async def get_site_stats(self) -> SiteStats:
        boards = await self.board_repo.list_all()
        thread_counts = await self.thread_repo.count_by_board()
        post_counts = await self.post_repo.count_by_board()
        online_counts = await self.online_tracker.count_by_board(
            [board.slug for board in boards]
        )
        online_total = await self.online_tracker.count_site()
        return SiteStats(
            boards=boards,
            thread_counts=thread_counts,
            post_counts=post_counts,
            online_counts=online_counts,
            online_total=online_total,
        )
