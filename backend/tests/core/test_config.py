from src.core.config import Settings, get_settings


def test_get_settings_returns_settings():
    assert isinstance(get_settings(), Settings)


def test_get_settings_is_cached():
    assert get_settings() is get_settings()
