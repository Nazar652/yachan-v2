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
    db_pool_recycle: int = 300
    # hold no idle connections; prod sets it so the neon compute can scale to zero
    db_use_null_pool: bool = False

    redis_url: str = "redis://localhost:6379/0"

    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24

    ip_hash_salt: str

    storage_backend: str = "local"
    storage_dir: str = "storage"
    storage_base_url: str = "/media"
    # absolute base url the moderation service fetches media from (dev: the in-network
    # minio endpoint; prod: the public bucket/cdn url). empty falls back to public_url
    media_internal_url: str = ""

    # onnx sentence-embedding model (multilingual MiniLM) used for semantic search;
    # baked into the image at build, paths are relative to the backend working dir
    embedding_model_path: str = "models/embedding.onnx"
    embedding_tokenizer_path: str = "models/tokenizer.json"

    # thread auto-summary via the gemini api; empty key disables the feature entirely
    gemini_api_key: str = ""
    summary_model: str = "gemini-3.1-flash-lite"

    s3_endpoint_url: str = ""
    s3_bucket: str = "yachan-media"
    s3_access_key: str = ""
    s3_secret_key: str = ""
    s3_region: str = "us-east-1"

    cors_origins: str = "http://localhost:5173"

    # error + performance monitoring; empty dsn disables the sdk entirely
    sentry_dsn: str = ""
    sentry_environment: str = "production"
    sentry_traces_sample_rate: float = 1.0

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
