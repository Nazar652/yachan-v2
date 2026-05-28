from kink import inject
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col

from src.models.post_edit import PostEdit

from .base import BaseRepository


@inject
class PostEditRepository(BaseRepository):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_by_post_id(self, post_id: int) -> PostEdit | None:
        result = await self.session.execute(
            select(PostEdit).where(col(PostEdit.post_id) == post_id)
        )
        return result.scalar_one_or_none()

    async def create(self, edit: PostEdit) -> PostEdit:
        self.session.add(edit)
        await self.session.flush()
        await self.session.refresh(edit)
        return edit
