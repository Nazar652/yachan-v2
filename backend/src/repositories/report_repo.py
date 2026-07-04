from kink import inject
from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col

from src.models.board import Board
from src.models.post import Post
from src.models.report import Report

from .base import BaseRepository


class ReportRepository(BaseRepository):
    @inject
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_by_id(self, report_id: int) -> Report | None:
        result = await self.session.execute(select(Report).where(col(Report.id) == report_id))
        return result.scalar_one_or_none()

    async def list_unresolved(
        self, board_id: int | None = None
    ) -> list[tuple[Report, int, int, str]]:
        # join through the post (not report.board_id, which is only set at report time)
        # so the returned board/thread always match where the post actually lives
        stmt = (
            select(Report, col(Post.post_number), col(Post.thread_id), col(Board.slug))
            .join(Post, col(Report.post_id) == col(Post.id))
            .join(Board, col(Post.board_id) == col(Board.id))
            .where(col(Report.is_resolved).is_(False))
        )
        if board_id is not None:
            stmt = stmt.where(col(Report.board_id) == board_id)
        result = await self.session.execute(stmt.order_by(col(Report.created_at).asc()))
        return [(report, post_number, thread_id, slug) for report, post_number, thread_id, slug in result.all()]

    async def create(self, report: Report) -> Report:
        self.session.add(report)
        await self.session.flush()
        await self.session.refresh(report)
        return report

    async def mark_resolved(self, report_id: int, resolved_by: int) -> None:
        await self.session.execute(
            update(Report)
            .where(col(Report.id) == report_id)
            .values(is_resolved=True, resolved_by=resolved_by)
        )

    async def delete_by_post_ids(self, post_ids: list[int]) -> None:
        if not post_ids:
            return
        await self.session.execute(
            delete(Report).where(col(Report.post_id).in_(post_ids))
        )

    async def count_unresolved_for_post(self, post_id: int) -> int:
        result = await self.session.execute(
            select(func.count())
            .select_from(Report)
            .where(col(Report.post_id) == post_id, col(Report.is_resolved).is_(False))
        )
        return result.scalar_one()

    async def count_unresolved_for_post_by_ip(self, post_id: int, ip_hash: str) -> int:
        result = await self.session.execute(
            select(func.count())
            .select_from(Report)
            .where(
                col(Report.post_id) == post_id,
                col(Report.ip_hash) == ip_hash,
                col(Report.is_resolved).is_(False),
            )
        )
        return result.scalar_one()

    async def count_auto_for_post(self, post_id: int) -> int:
        result = await self.session.execute(
            select(func.count())
            .select_from(Report)
            .where(col(Report.post_id) == post_id, col(Report.is_auto).is_(True))
        )
        return result.scalar_one()
