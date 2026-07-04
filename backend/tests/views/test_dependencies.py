import pytest
from src.core.exceptions import UnauthorizedError
from src.utils.ip import hash_ip
from src.views.dependencies import bearer_token, client_ip_hash, optional_bearer_token
from tests.views._factories import request_ns, settings_ns


def test_client_ip_hash_matches_hash_ip():
    settings = settings_ns()
    result = client_ip_hash(request_ns("9.9.9.9"), settings)
    assert result == hash_ip("9.9.9.9", "salt")


def test_client_ip_hash_prefers_x_real_ip():
    settings = settings_ns()
    result = client_ip_hash(request_ns("9.9.9.9", headers={"x-real-ip": "5.6.7.8"}), settings)
    assert result == hash_ip("5.6.7.8", "salt")


def test_client_ip_hash_handles_missing_client():
    from types import SimpleNamespace

    settings = settings_ns()
    result = client_ip_hash(SimpleNamespace(client=None, headers={}), settings)
    assert result == hash_ip("unknown", "salt")


def test_bearer_token_extracts_value():
    assert bearer_token("Bearer abc.def") == "abc.def"
    assert bearer_token("bearer xyz") == "xyz"


def test_bearer_token_rejects_missing():
    with pytest.raises(UnauthorizedError):
        bearer_token(None)


def test_bearer_token_rejects_wrong_scheme():
    with pytest.raises(UnauthorizedError):
        bearer_token("Basic abc")


def test_optional_bearer_token_extracts_value():
    assert optional_bearer_token("Bearer abc.def") == "abc.def"


def test_optional_bearer_token_returns_none_when_missing():
    assert optional_bearer_token(None) is None


def test_optional_bearer_token_returns_none_for_wrong_scheme():
    assert optional_bearer_token("Basic abc") is None
