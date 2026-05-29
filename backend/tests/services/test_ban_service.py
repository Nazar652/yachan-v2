from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from src.core.exceptions import IpBannedError
from src.services.ban_service import BanService


def _service(ban_repo):
    return BanService(ban_repo=ban_repo)


async def test_assert_not_banned_passes_when_no_ban():
    ban_repo = MagicMock()
    ban_repo.get_active_for_ip = AsyncMock(return_value=None)
    service = _service(ban_repo)

    await service.assert_not_banned("hash", board_id=1)


async def test_assert_not_banned_raises_when_banned():
    ban_repo = MagicMock()
    ban_repo.get_active_for_ip = AsyncMock(return_value=SimpleNamespace(reason="spam"))
    service = _service(ban_repo)

    with pytest.raises(IpBannedError):
        await service.assert_not_banned("hash", board_id=1)


async def test_create_ban_delegates_to_repo():
    created = object()
    ban_repo = MagicMock()
    ban_repo.create = AsyncMock(return_value=created)
    service = _service(ban_repo)

    result = await service.create_ban("hash", 1, "spam", None, created_by=2)

    assert result is created
    ban_repo.create.assert_awaited_once()


async def test_expire_due_delegates():
    ban_repo = MagicMock()
    ban_repo.deactivate_expired = AsyncMock(return_value=4)
    service = _service(ban_repo)

    assert await service.expire_due() == 4
