from src.core.config import Settings, get_settings


def test_get_settings_returns_settings():
    assert isinstance(get_settings(), Settings)


def test_get_settings_is_cached():
    assert get_settings() is get_settings()


def test_db_use_null_pool_defaults_off():
    assert Settings().db_use_null_pool is False


def test_cors_origin_list_splits_comma_string():
    settings = Settings(cors_origins="http://a.com, http://b.com")
    assert settings.cors_origin_list == ["http://a.com", "http://b.com"]


def test_cors_origin_list_ignores_blanks():
    settings = Settings(cors_origins="http://a.com,, ")
    assert settings.cors_origin_list == ["http://a.com"]
