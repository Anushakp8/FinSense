"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """FinSense application settings.

    All values are loaded from environment variables or a .env file.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # â”€â”€ PostgreSQL â”€â”€
    postgres_user: str = "finsense"
    postgres_password: str = "finsense_secret"
    postgres_db: str = "finsense"
    postgres_port: int = 5432
    database_url: str = (
        "postgresql+asyncpg://finsense:finsense_secret@localhost:5432/finsense"
    )
    database_url_sync: str = (
        "postgresql+psycopg2://finsense:finsense_secret@localhost:5432/finsense"
    )

    # â”€â”€ Redis â”€â”€
    redis_url: str = "redis://localhost:6379/0"

    # â”€â”€ Kafka â”€â”€
    kafka_bootstrap_servers: str = "localhost:9092"

    # â”€â”€ FRED API â”€â”€
    fred_api_key: str = ""

    # â”€â”€ FastAPI â”€â”€
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_cors_origins: list[str] = ["http://localhost:3000"]

    # â”€â”€ Model Storage â”€â”€
    model_artifacts_path: str = "./models"

    # â”€â”€ Application â”€â”€
    environment: str = "development"
    log_level: str = "INFO"


# Singleton instance
settings = Settings()
