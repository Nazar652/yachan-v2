from kink import inject
from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col

from src.models.thread import Thread

from .base import BaseRepository


class ThreadRepository(BaseRepository):
    @inject
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_by_id(self, thread_id: int) -> Thread | None:
        result = await self.session.execute(select(Thread).where(col(Thread.id) == thread_id))
        return result.scalar_one_or_none()

    async def list_by_board(
        self, board_id: int, limit: int = 50, offset: int = 0
    ) -> list[Thread]:
        result = await self.session.execute(
            select(Thread)
            .where(col(Thread.board_id) == board_id)
            .order_by(col(Thread.is_sticky).desc(), col(Thread.bump_at).desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def list_latest(self, limit: int = 5) -> list[Thread]:
        result = await self.session.execute(
            select(Thread).order_by(col(Thread.bump_at).desc()).limit(limit)
        )
        return list(result.scalars().all())

    async def count_by_board(self) -> dict[int, int]:
        result = await self.session.execute(
            select(col(Thread.board_id), func.count()).group_by(col(Thread.board_id))
        )
        return {board_id: count for board_id, count in result.all()}

    async def create(self, thread: Thread) -> Thread:
        self.session.add(thread)
        await self.session.flush()
        await self.session.refresh(thread)
        return thread

    async def set_reply_count(self, thread_id: int, count: int) -> None:
        await self.session.execute(
            update(Thread).where(col(Thread.id) == thread_id).values(reply_count=count)
        )

    async def update_bump_at(self, thread_id: int) -> None:
        await self.session.execute(
            update(Thread).where(col(Thread.id) == thread_id).values(bump_at=func.now())
        )

    async def set_locked(self, thread_id: int, locked: bool) -> None:
        await self.session.execute(
            update(Thread).where(col(Thread.id) == thread_id).values(is_locked=locked)
        )

    async def set_sticky(self, thread_id: int, sticky: bool) -> None:
        await self.session.execute(
            update(Thread).where(col(Thread.id) == thread_id).values(is_sticky=sticky)
        )

    async def delete(self, thread_id: int) -> None:
        await self.session.execute(delete(Thread).where(col(Thread.id) == thread_id))
