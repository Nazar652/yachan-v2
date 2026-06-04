from kink import inject
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col

from src.models.report import Report

from .base import BaseRepository


class ReportRepository(BaseRepository):
    @inject
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_by_id(self, report_id: int) -> Report | None:
        result = await self.session.execute(select(Report).where(col(Report.id) == report_id))
        return result.scalar_one_or_none()

    async def list_unresolved(self, board_id: int | None = None) -> list[Report]:
        stmt = select(Report).where(col(Report.is_resolved).is_(False))
        if board_id is not None:
            stmt = stmt.where(col(Report.board_id) == board_id)
        result = await self.session.execute(stmt.order_by(col(Report.created_at).asc()))
        return list(result.scalars().all())

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

    async def count_unresolved_for_post(self, post_id: int) -> int:
        result = await self.session.execute(
            select(func.count())
            .select_from(Report)
            .where(col(Report.post_id) == post_id, col(Report.is_resolved).is_(False))
        )
        return result.scalar_one()
