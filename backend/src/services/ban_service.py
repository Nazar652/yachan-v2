from datetime import datetime

from kink import inject

from src.core.exceptions import IpBannedError
from src.models.ban import Ban
from src.repositories.ban_repo import BanRepository
from src.utils.clock import utcnow


@inject
class BanService:
    def __init__(self, ban_repo: BanRepository) -> None:
        self.ban_repo = ban_repo

    async def assert_not_banned(self, ip_hash: str, board_id: int) -> None:
        ban = await self.ban_repo.get_active_for_ip(ip_hash, board_id, utcnow())
        if ban is not None:
            raise IpBannedError(ban.reason or "banned")

    async def create_ban(
        self,
        ip_hash: str,
        board_id: int | None,
        reason: str | None,
        expires_at: datetime | None,
        created_by: int | None,
    ) -> Ban:
        return await self.ban_repo.create(
            Ban(
                ip_hash=ip_hash,
                board_id=board_id,
                reason=reason,
                expires_at=expires_at,
                created_by=created_by,
            )
        )

    async def lift_ban(self, ban_id: int) -> None:
        await self.ban_repo.deactivate(ban_id)

    async def list_active(self) -> list[Ban]:
        return await self.ban_repo.list_active()

    async def expire_due(self) -> int:
        return await self.ban_repo.deactivate_expired(utcnow())
