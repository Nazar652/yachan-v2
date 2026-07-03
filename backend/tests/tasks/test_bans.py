from unittest.mock import AsyncMock, MagicMock

from kink import di

from src.services.ban_service import BanService
from src.tasks.bans import expire_bans


def test_expire_bans_delegates_and_returns_count(monkeypatch):
    instance = MagicMock()
    instance.expire_due = AsyncMock(return_value=3)
    monkeypatch.setitem(di.factories, BanService, lambda container: instance)

    assert expire_bans() == 3
    instance.expire_due.assert_awaited_once()
