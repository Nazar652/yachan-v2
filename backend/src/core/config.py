from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# absolute path to backend/.env so it is found regardless of the current
# working directory (app, alembic and pre-push hooks run from different cwds)
_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "yachan-v2 API"
    app_version: str = "0.1.0"
    debug: bool = False

    database_url: str = "postgresql+asyncpg://yachan:yachan@localhost:5432/yachan"
    db_echo: bool = False

    redis_url: str = "redis://localhost:6379/0"

    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24

    ip_hash_salt: str

    storage_dir: str = "storage"
    storage_base_url: str = "/media"


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
