from unittest.mock import AsyncMock, MagicMock

import src.tasks.bans as bans_task
from src.tasks.bans import expire_bans


def test_expire_bans_delegates_and_returns_count(monkeypatch):
    instance = MagicMock()
    instance.expire_due = AsyncMock(return_value=3)
    factory = MagicMock(return_value=instance)
    monkeypatch.setattr(bans_task, "BanService", factory)

    assert expire_bans() == 3
    instance.expire_due.assert_awaited_once()
