from kink import inject
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col

from src.models.mod_account import ModAccount

from .base import BaseRepository


@inject
class ModAccountRepository(BaseRepository):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_by_id(self, account_id: int) -> ModAccount | None:
        result = await self.session.execute(
            select(ModAccount).where(col(ModAccount.id) == account_id)
        )
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> ModAccount | None:
        result = await self.session.execute(
            select(ModAccount).where(col(ModAccount.username) == username)
        )
        return result.scalar_one_or_none()

    async def create(self, account: ModAccount) -> ModAccount:
        self.session.add(account)
        await self.session.flush()
        await self.session.refresh(account)
        return account
