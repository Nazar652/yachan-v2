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

    # "local" writes to the filesystem, "s3" to an S3-compatible object store
    # (MinIO in docker, AWS S3 in production)
    storage_backend: str = "local"
    storage_dir: str = "storage"
    # public base url the serializer prepends to a key; nginx maps it to the
    # files volume (local) or proxies it to the object store (s3)
    storage_base_url: str = "/media"

    s3_endpoint_url: str = ""
    s3_bucket: str = "yachan-media"
    s3_access_key: str = ""
    s3_secret_key: str = ""
    s3_region: str = "us-east-1"

    # browser origins allowed to call the api, comma-separated
    cors_origins: str = "http://localhost:5173"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
