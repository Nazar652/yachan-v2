from kink import inject

from src.core.exceptions import BoardNotFoundError, PostNotFoundError
from src.models.report import Report
from src.repositories.board_repo import BoardRepository
from src.repositories.post_repo import PostRepository
from src.repositories.report_repo import ReportRepository
from src.schemas.report import ReportCreate

# reporter ip stored on an auto-report; a sentinel since no human filed it
_AUTO_REPORTER = "auto-moderation"
# verdict keys -> human-readable reason parts for the auto-report
_VERDICT_LABELS = {"toxic": "toxicity", "spam": "spam"}


class ReportService:
    @inject
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

    async def apply_text_verdict(self, post_id: int, verdict: dict[str, object]) -> Report | None:
        labels = [name for key, name in _VERDICT_LABELS.items() if verdict.get(key)]
        if not labels:
            return None
        return await self.create_auto_report(post_id, "Auto-flagged: " + ", ".join(labels))

    async def create_auto_report(self, post_id: int, reason: str) -> Report | None:
        # one auto-report per post: don't pile on if moderation already flagged it
        if await self.report_repo.count_auto_for_post(post_id) > 0:
            return None

        post = await self.post_repo.get_by_id(post_id)
        if post is None:
            return None

        return await self.report_repo.create(
            Report(
                post_id=post_id,
                board_id=post.board_id,
                reason=reason,
                ip_hash=_AUTO_REPORTER,
                is_auto=True,
            )
        )

    async def list_unresolved(self, board_id: int | None = None) -> list[Report]:
        return await self.report_repo.list_unresolved(board_id)

    async def resolve(self, report_id: int, mod_id: int) -> None:
        await self.report_repo.mark_resolved(report_id, mod_id)
