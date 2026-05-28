from kink import inject

from src.core.exceptions import BoardNotFoundError, PostNotFoundError
from src.models.report import Report
from src.repositories.board_repo import BoardRepository
from src.repositories.post_repo import PostRepository
from src.repositories.report_repo import ReportRepository
from src.schemas.report import ReportCreate


@inject
class ReportService:
    def __init__(
        self,
        report_repo: ReportRepository,
        post_repo: PostRepository,
        board_repo: BoardRepository,
    ) -> None:
        self.report_repo = report_repo
        self.post_repo = post_repo
        self.board_repo = board_repo

    async def create_report(
        self, board_slug: str, post_number: int, data: ReportCreate, ip_hash: str
    ) -> Report:
        board = await self.board_repo.get_by_slug(board_slug)
        if board is None:
            raise BoardNotFoundError(board_slug)

        post = await self.post_repo.get_by_board_and_number(board.id, post_number)
        if post is None:
            raise PostNotFoundError(post_number)

        return await self.report_repo.create(
            Report(post_id=post.id, board_id=board.id, reason=data.reason, ip_hash=ip_hash)
        )

    async def list_unresolved(self, board_id: int | None = None) -> list[Report]:
        return await self.report_repo.list_unresolved(board_id)

    async def resolve(self, report_id: int, mod_id: int) -> None:
        await self.report_repo.mark_resolved(report_id, mod_id)
