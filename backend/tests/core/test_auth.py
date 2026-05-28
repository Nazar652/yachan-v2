import jwt
import pytest

from src.core.auth import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from src.core.config import get_settings


def test_hash_then_verify_succeeds():
    encoded = hash_password("hunter2")
    assert verify_password("hunter2", encoded) is True


def test_verify_rejects_wrong_password():
    encoded = hash_password("hunter2")
    assert verify_password("wrong", encoded) is False


def test_hash_is_salted_so_outputs_differ():
    assert hash_password("same") != hash_password("same")


def test_verify_handles_malformed_encoded():
    assert verify_password("pw", "not-a-valid-hash") is False


def test_jwt_roundtrip():
    settings = get_settings()
    token = create_access_token("42", settings)
    payload = decode_access_token(token, settings)
    assert payload["sub"] == "42"


def test_decode_rejects_tampered_token():
    settings = get_settings()
    token = create_access_token("42", settings)
    with pytest.raises(jwt.InvalidTokenError):
        decode_access_token(token + "tampered", settings)
