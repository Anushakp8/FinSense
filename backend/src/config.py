"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """FinSense application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    postgres_user: str = "finsense"
    postgres_password: str = "finsense_secret"
    postgres_db: str = "finsense"
    postgres_port: int = 5432
    database_url: str = "postgresql+asyncpg://finsense:finsense_secret@localhost:5432/finsense"
    database_url_sync: str = "postgresql+psycopg2://finsense:finsense_secret@localhost:5432/finsense"
    redis_url: str = "redis://localhost:6379/0"
    kafka_bootstrap_servers: str = "localhost:9092"
    fred_api_key: str = ""
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_cors_origins: list[str] = ["http://localhost:3000"]
    api_require_key: bool = False
    api_key: str = ""
    api_rate_limit_enabled: bool = False
    api_rate_limit_use_redis: bool = True
    api_rate_limit_max_requests: int = 60
    api_rate_limit_window_seconds: int = 60
    model_artifacts_path: str = "./models"
    environment: str = "development"
    log_level: str = "INFO"


settings = Settings()
