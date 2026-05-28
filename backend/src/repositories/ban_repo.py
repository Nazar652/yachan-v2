from datetime import datetime
from typing import cast

from kink import inject
from sqlalchemy import or_, select, update
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col

from src.models.ban import Ban

from .base import BaseRepository


@inject
class BanRepository(BaseRepository):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_active_for_ip(
        self, ip_hash: str, board_id: int | None, now: datetime
    ) -> Ban | None:
        # a ban applies if it is global (board_id is null) or matches this board,
        # and it is active and not yet expired
        result = await self.session.execute(
            select(Ban).where(
                col(Ban.ip_hash) == ip_hash,
                col(Ban.is_active).is_(True),
                or_(col(Ban.board_id).is_(None), col(Ban.board_id) == board_id),
                or_(col(Ban.expires_at).is_(None), col(Ban.expires_at) > now),
            )
        )
        return result.scalars().first()

    async def list_active(self) -> list[Ban]:
        result = await self.session.execute(select(Ban).where(col(Ban.is_active).is_(True)))
        return list(result.scalars().all())

    async def create(self, ban: Ban) -> Ban:
        self.session.add(ban)
        await self.session.flush()
        await self.session.refresh(ban)
        return ban

    async def deactivate(self, ban_id: int) -> None:
        await self.session.execute(
            update(Ban).where(col(Ban.id) == ban_id).values(is_active=False)
        )

    async def deactivate_expired(self, now: datetime) -> int:
        result = await self.session.execute(
            update(Ban)
            .where(
                col(Ban.is_active).is_(True),
                col(Ban.expires_at).is_not(None),
                col(Ban.expires_at) <= now,
            )
            .values(is_active=False)
        )
        return cast(CursorResult, result).rowcount
