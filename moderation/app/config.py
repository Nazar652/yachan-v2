from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    redis_url: str = "redis://localhost:6379/0"
    fetch_timeout_seconds: float = 15.0
    onnx_model_path: str = "models/image-safety-classifier-xs.onnx"
    # multilingual distilbert toxicity classifier; blatant toxicity above this score
    toxicity_model_path: str = "models/toxicity.onnx"
    toxicity_tokenizer_path: str = "models/toxicity-tokenizer.json"
    toxicity_threshold: float = 0.8


settings = Settings()
