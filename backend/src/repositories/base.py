from kink import inject
from sqlalchemy.ext.asyncio import AsyncSession


@inject
class BaseRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session  # shared with all repos in the same request

    async def flush(self) -> None:
        await self.session.flush()

    async def refresh(self, instance: object) -> None:
        await self.session.refresh(instance)
