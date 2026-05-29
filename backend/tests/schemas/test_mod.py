from datetime import datetime
from types import SimpleNamespace

import pytest
from pydantic import ValidationError
from src.models.mod_account import ModRole
from src.schemas.mod import BanCreate, ModAccountResponse, ModLogin, TokenResponse


def test_mod_login_requires_non_empty():
    with pytest.raises(ValidationError):
        ModLogin(username="", password="")


def test_token_response_defaults_bearer():
    assert TokenResponse(access_token="abc").token_type == "bearer"


def test_mod_account_response_hides_password_hash():
    obj = SimpleNamespace(
        id=1,
        username="admin",
        role=ModRole.ADMIN,
        is_active=True,
        created_at=datetime(2026, 1, 1),
        password_hash="secret",
    )
    response = ModAccountResponse.model_validate(obj)
    assert "password_hash" not in response.model_dump()


def test_ban_create_defaults():
    ban = BanCreate()
    assert ban.reason is None
    assert ban.expires_at is None
    assert ban.board_id is None
