from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from src.core.config import get_settings
from src.core.exceptions import (
    InvalidCredentialsError,
    ModAccountExistsError,
    ModInactiveError,
    PostNotFoundError,
)
from src.models.mod_account import ModRole
from src.schemas.mod import BanCreate
from src.services.mod_service import ModService
from src.utils.auth import create_access_token, hash_password, verify_password


def build(**repos):
    defaults = {
        "mod_account_repo": MagicMock(),
        "post_repo": MagicMock(),
        "thread_repo": MagicMock(),
        "board_repo": MagicMock(),
        "ban_service": MagicMock(),
    }
    defaults.update(repos)
    service = ModService(settings=get_settings(), **defaults)
    return service, SimpleNamespace(**defaults)


async def test_create_account_hashes_password_and_persists():
    created = SimpleNamespace(id=1, username="root")
    mod_account_repo = MagicMock()
    mod_account_repo.get_by_username = AsyncMock(return_value=None)
    mod_account_repo.create = AsyncMock(return_value=created)
    service, _ = build(mod_account_repo=mod_account_repo)

    result = await service.create_account("root", "pw", ModRole.ADMIN)

    assert result is created
    stored = mod_account_repo.create.await_args.args[0]
    assert stored.username == "root"
    assert stored.role is ModRole.ADMIN
    assert stored.password_hash != "pw"
    assert verify_password("pw", stored.password_hash)


async def test_create_account_rejects_duplicate_username():
    mod_account_repo = MagicMock()
    mod_account_repo.get_by_username = AsyncMock(return_value=SimpleNamespace(id=1))
    mod_account_repo.create = AsyncMock()
    service, _ = build(mod_account_repo=mod_account_repo)

    with pytest.raises(ModAccountExistsError):
        await service.create_account("root", "pw", ModRole.ADMIN)
    mod_account_repo.create.assert_not_called()


async def test_authenticate_returns_token():
    account = SimpleNamespace(
        id=1, password_hash=hash_password("pw"), is_active=True
    )
    mod_account_repo = MagicMock()
    mod_account_repo.get_by_username = AsyncMock(return_value=account)
    service, _ = build(mod_account_repo=mod_account_repo)

    token = await service.authenticate("admin", "pw")
    assert isinstance(token, str) and token


async def test_authenticate_wrong_password():
    account = SimpleNamespace(id=1, password_hash=hash_password("pw"), is_active=True)
    mod_account_repo = MagicMock()
    mod_account_repo.get_by_username = AsyncMock(return_value=account)
    service, _ = build(mod_account_repo=mod_account_repo)

    with pytest.raises(InvalidCredentialsError):
        await service.authenticate("admin", "wrong")


async def test_authenticate_unknown_user():
    mod_account_repo = MagicMock()
    mod_account_repo.get_by_username = AsyncMock(return_value=None)
    service, _ = build(mod_account_repo=mod_account_repo)

    with pytest.raises(InvalidCredentialsError):
        await service.authenticate("ghost", "pw")


async def test_authenticate_inactive_account():
    account = SimpleNamespace(id=1, password_hash=hash_password("pw"), is_active=False)
    mod_account_repo = MagicMock()
    mod_account_repo.get_by_username = AsyncMock(return_value=account)
    service, _ = build(mod_account_repo=mod_account_repo)

    with pytest.raises(ModInactiveError):
        await service.authenticate("admin", "pw")


async def test_resolve_mod_valid_token():
    account = SimpleNamespace(id=7, is_active=True)
    mod_account_repo = MagicMock()
    mod_account_repo.get_by_id = AsyncMock(return_value=account)
    service, _ = build(mod_account_repo=mod_account_repo)
    token = create_access_token("7", get_settings())

    assert await service.resolve_mod(token) is account


async def test_resolve_mod_invalid_token():
    service, _ = build()
    with pytest.raises(InvalidCredentialsError):
        await service.resolve_mod("garbage.token.value")


async def test_resolve_mod_inactive():
    mod_account_repo = MagicMock()
    mod_account_repo.get_by_id = AsyncMock(return_value=SimpleNamespace(id=7, is_active=False))
    service, _ = build(mod_account_repo=mod_account_repo)
    token = create_access_token("7", get_settings())

    with pytest.raises(ModInactiveError):
        await service.resolve_mod(token)


async def test_delete_post_soft_deletes_with_mod_id():
    board_repo = MagicMock()
    board_repo.get_by_slug = AsyncMock(return_value=SimpleNamespace(id=1))
    post_repo = MagicMock()
    post_repo.get_by_board_and_number = AsyncMock(return_value=SimpleNamespace(id=10))
    post_repo.soft_delete = AsyncMock()
    service, _ = build(board_repo=board_repo, post_repo=post_repo)

    await service.delete_post("b", 5, SimpleNamespace(id=99))

    post_repo.soft_delete.assert_awaited_once_with(10, deleted_by=99)


async def test_delete_post_missing_post():
    board_repo = MagicMock()
    board_repo.get_by_slug = AsyncMock(return_value=SimpleNamespace(id=1))
    post_repo = MagicMock()
    post_repo.get_by_board_and_number = AsyncMock(return_value=None)
    service, _ = build(board_repo=board_repo, post_repo=post_repo)

    with pytest.raises(PostNotFoundError):
        await service.delete_post("b", 5, SimpleNamespace(id=99))


async def test_ban_poster_uses_post_ip_hash():
    board_repo = MagicMock()
    board_repo.get_by_slug = AsyncMock(return_value=SimpleNamespace(id=1))
    post_repo = MagicMock()
    post_repo.get_by_board_and_number = AsyncMock(
        return_value=SimpleNamespace(id=10, ip_hash="poster-hash")
    )
    ban_service = MagicMock()
    ban_service.create_ban = AsyncMock(return_value=SimpleNamespace(id=1))
    service, _ = build(board_repo=board_repo, post_repo=post_repo, ban_service=ban_service)

    await service.ban_poster("b", 5, BanCreate(reason="spam"), SimpleNamespace(id=99))

    ban_service.create_ban.assert_awaited_once()
    assert ban_service.create_ban.await_args.kwargs["ip_hash"] == "poster-hash"
    assert ban_service.create_ban.await_args.kwargs["created_by"] == 99


async def test_set_thread_locked():
    board_repo = MagicMock()
    board_repo.get_by_slug = AsyncMock(return_value=SimpleNamespace(id=1))
    thread_repo = MagicMock()
    thread_repo.get_by_id = AsyncMock(return_value=SimpleNamespace(id=5, board_id=1))
    thread_repo.set_locked = AsyncMock()
    service, _ = build(board_repo=board_repo, thread_repo=thread_repo)

    await service.set_thread_locked("b", 5, True)

    thread_repo.set_locked.assert_awaited_once_with(5, True)
