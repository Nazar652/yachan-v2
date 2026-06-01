from kink import inject
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col

from src.models.post_backlink import PostBacklink

from .base import BaseRepository


@inject
class PostBacklinkRepository(BaseRepository):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def list_sources_for_target(self, target_post_id: int) -> list[PostBacklink]:
        # who replied to this post
        result = await self.session.execute(
            select(PostBacklink).where(col(PostBacklink.target_post_id) == target_post_id)
        )
        return list(result.scalars().all())

    async def list_targets_for_source(self, source_post_id: int) -> list[PostBacklink]:
        # which posts this one links to
        result = await self.session.execute(
            select(PostBacklink).where(col(PostBacklink.source_post_id) == source_post_id)
        )
        return list(result.scalars().all())

    async def create_many(self, links: list[PostBacklink]) -> None:
        self.session.add_all(links)
        await self.session.flush()
