from src.utils.request_context import get_request_id, new_id, set_request_id


def test_default_is_none():
    assert get_request_id() is None


def test_set_and_get_roundtrip():
    set_request_id("abc123")
    assert get_request_id() == "abc123"
    set_request_id(None)
    assert get_request_id() is None


def test_new_id_returns_unique_hex_strings():
    first = new_id()
    second = new_id()
    assert first != second
    assert len(first) == 32
    int(first, 16)  # valid hex
