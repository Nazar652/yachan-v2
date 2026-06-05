from kink import inject
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col

from src.models.attachment import Attachment, MediaType

from .base import BaseRepository


class AttachmentRepository(BaseRepository):
    @inject
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_by_id(self, attachment_id: int) -> Attachment | None:
        result = await self.session.execute(
            select(Attachment).where(col(Attachment.id) == attachment_id)
        )
        return result.scalar_one_or_none()

    async def get_by_md5(self, md5: str) -> Attachment | None:
        result = await self.session.execute(
            select(Attachment).where(col(Attachment.md5) == md5)
        )
        return result.scalar_one_or_none()

    async def get_first_images_by_post_ids(self, post_ids: list[int]) -> dict[int, Attachment]:
        if not post_ids:
            return {}
        subquery = (
            select(func.min(col(Attachment.id)))
            .where(
                col(Attachment.post_id).in_(post_ids),
                col(Attachment.media_type) == MediaType.IMAGE,
            )
            .group_by(col(Attachment.post_id))
            .scalar_subquery()
        )
        result = await self.session.execute(
            select(Attachment).where(col(Attachment.id).in_(subquery))
        )
        return {att.post_id: att for att in result.scalars().all()}

    async def list_by_post(self, post_id: int) -> list[Attachment]:
        result = await self.session.execute(
            select(Attachment).where(col(Attachment.post_id) == post_id)
        )
        return list(result.scalars().all())

    async def create(self, attachment: Attachment) -> Attachment:
        self.session.add(attachment)
        await self.session.flush()
        await self.session.refresh(attachment)
        return attachment

    async def set_media_info(
        self,
        attachment_id: int,
        *,
        thumbnail_path: str | None,
        width: int | None,
        height: int | None,
        duration_seconds: float | None,
    ) -> None:
        await self.session.execute(
            update(Attachment)
            .where(col(Attachment.id) == attachment_id)
            .values(
                thumbnail_path=thumbnail_path,
                width=width,
                height=height,
                duration_seconds=duration_seconds,
            )
        )
