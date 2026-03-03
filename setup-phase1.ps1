# FinSense Phase 1 Setup Script
# Run from: F:\Masters personal projects\finsense
# Usage: powershell -ExecutionPolicy Bypass -File setup-phase1.ps1

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot

Write-Host "Setting up FinSense Phase 1 files..." -ForegroundColor Cyan

# Create all directories
$dirs = @(
    "backend/alembic/versions",
    "backend/src/models",
    "backend/src/ingestion",
    "backend/src/features",
    "backend/src/ml",
    "backend/src/api/routes",
    "backend/src/dags",
    "backend/tests/test_ingestion",
    "backend/tests/test_features",
    "backend/tests/test_ml",
    "backend/tests/test_api",
    "frontend/src/app/predictions",
    "frontend/src/app/portfolio",
    "frontend/src/app/pipeline",
    "frontend/src/components/layout",
    "frontend/src/components/charts",
    "frontend/src/components/cards",
    "frontend/src/components/skeletons",
    "frontend/src/components/common",
    "frontend/src/hooks",
    "frontend/src/lib",
    "frontend/src/theme",
    "frontend/src/types",
    "frontend/public",
    "docs",
    "tasks",
    "scripts"
)

foreach ($d in $dirs) {
    $path = Join-Path $root $d
    if (!(Test-Path $path)) {
        New-Item -ItemType Directory -Path $path -Force | Out-Null
        Write-Host "  Created: $d" -ForegroundColor DarkGray
    }
}

# Create empty __init__.py files
$initFiles = @(
    "backend/src/__init__.py",
    "backend/src/api/__init__.py",
    "backend/src/api/routes/__init__.py",
    "backend/src/features/__init__.py",
    "backend/src/ingestion/__init__.py",
    "backend/src/ml/__init__.py",
    "backend/tests/__init__.py",
    "backend/tests/test_ingestion/__init__.py",
    "backend/tests/test_features/__init__.py",
    "backend/tests/test_ml/__init__.py",
    "backend/tests/test_api/__init__.py"
)

foreach ($f in $initFiles) {
    $path = Join-Path $root $f
    if (!(Test-Path $path)) {
        New-Item -ItemType File -Path $path -Force | Out-Null
    }
}

# ── .env.example ──
@'
# FinSense Environment Variables
# Copy this file to .env and fill in your values

# PostgreSQL
POSTGRES_USER=finsense
POSTGRES_PASSWORD=finsense_secret
POSTGRES_DB=finsense
POSTGRES_PORT=5432
DATABASE_URL=postgresql+asyncpg://finsense:finsense_secret@localhost:5432/finsense
DATABASE_URL_SYNC=postgresql+psycopg2://finsense:finsense_secret@localhost:5432/finsense

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_PORT=6379

# Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_PORT=9092

# Airflow
AIRFLOW_DB=airflow
AIRFLOW_ADMIN_USER=admin
AIRFLOW_ADMIN_PASSWORD=admin
AIRFLOW_PORT=8080
AIRFLOW_FERNET_KEY=

# FRED API
FRED_API_KEY=your_fred_api_key_here

# FastAPI
API_HOST=0.0.0.0
API_PORT=8000
API_CORS_ORIGINS=["http://localhost:3000"]

# Model Storage
MODEL_ARTIFACTS_PATH=./models

# Application
ENVIRONMENT=development
LOG_LEVEL=INFO
'@ | Set-Content (Join-Path $root ".env.example") -Encoding UTF8

# ── .gitignore ──
@'
__pycache__/
*.py[cod]
*$py.class
*.egg-info/
dist/
build/
.eggs/
*.egg
.mypy_cache/
.ruff_cache/
.pytest_cache/
htmlcov/
.coverage
*.pkl
*.joblib
.venv/
venv/
env/
node_modules/
.next/
out/
bun.lockb
.env
.env.local
.env.*.local
docker-compose.override.yml
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store
models/
*.onnx
*.h5
logs/
*.log
airflow/logs/
'@ | Set-Content (Join-Path $root ".gitignore") -Encoding UTF8

# ── README.md ──
@'
# FinSense — Real-Time Financial Data Pipeline with ML Predictions

An end-to-end financial data engineering project that ingests real-time stock and economic data, transforms it through a structured pipeline, trains ML models for price movement prediction, and serves predictions through a FastAPI backend with a professional Next.js dashboard.

## Tech Stack

**Backend**: Python 3.12+, PostgreSQL 16 + TimescaleDB, Apache Kafka, Apache Airflow, FastAPI, Redis, scikit-learn, XGBoost

**Frontend**: Next.js 15, TypeScript (strict), Material UI v6, TanStack Query v5, Recharts, GSAP

**Infrastructure**: Docker Compose, GitHub Actions

## Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/yourusername/finsense.git
cd finsense

# 2. Copy environment variables
cp .env.example .env

# 3. Start infrastructure
docker compose up -d

# 4. Run database migrations
cd backend
alembic upgrade head

# 5. Start the API server
uvicorn src.api.main:app --reload

# 6. Start the frontend
cd frontend
bun install
bun run dev
```

## Project Status

- [x] Phase 1: Project Scaffolding and Infrastructure
- [ ] Phase 2: Data Ingestion Pipeline
- [ ] Phase 3: Feature Engineering Pipeline
- [ ] Phase 4: Airflow Orchestration
- [ ] Phase 5: ML Model Training and Versioning
- [ ] Phase 6: FastAPI Backend
- [ ] Phase 7: Frontend Dashboard — Setup and Layout
- [ ] Phase 8: Frontend Dashboard — Pages and Data Integration
- [ ] Phase 9: Integration Testing, Polish, and Documentation
- [ ] Phase 10: Backtest Report and Final Commit
'@ | Set-Content (Join-Path $root "README.md") -Encoding UTF8

# ── scripts/init-db.sh ──
@'
#!/bin/bash
set -e
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE DATABASE airflow;
    CREATE EXTENSION IF NOT EXISTS timescaledb;
EOSQL
'@ | Set-Content (Join-Path $root "scripts/init-db.sh") -Encoding UTF8

# ── tasks/todo.md ──
@'
# FinSense — Task Tracking

## Phase 1: Project Scaffolding and Infrastructure

**Goal**: Set up the full project structure, Docker environment, and database schema.

### Tasks

- [x] 1.1 Create the full folder structure
- [x] 1.2 Create docker-compose.yml with all services
- [x] 1.3 Create .env.example
- [x] 1.4 Create backend/pyproject.toml
- [x] 1.5 Initialize Alembic for database migrations
- [x] 1.6 Write SQLAlchemy ORM models for all four tables
- [x] 1.7 Generate initial Alembic migration with TimescaleDB hypertable
- [x] 1.8 Create tasks/lessons.md
- [x] 1.9 Create .gitignore
- [x] 1.10 Create initial README.md
- [x] 1.11 ER diagram reviewed and approved
'@ | Set-Content (Join-Path $root "tasks/todo.md") -Encoding UTF8

# ── tasks/lessons.md ──
@'
# FinSense — Lessons Learned

## Lessons

### 1. No `version` key in docker-compose.yml
**Rule**: Never include `version: "3.x"` in docker-compose.yml files.

### 2. Verify Docker image tags exist before using them
**Rule**: Always check Docker Hub for exact available tags.

### 3. Use `docker compose` (no hyphen) on modern Docker
**Rule**: The standalone `docker-compose` binary is deprecated.
'@ | Set-Content (Join-Path $root "tasks/lessons.md") -Encoding UTF8

# ── backend/pyproject.toml ──
@'
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "finsense"
version = "0.1.0"
description = "Real-time financial data pipeline with ML predictions"
requires-python = ">=3.12"
dependencies = [
    "sqlalchemy[asyncio]>=2.0,<3.0",
    "asyncpg>=0.29.0",
    "psycopg2-binary>=2.9.9",
    "alembic>=1.13.0",
    "yfinance>=0.2.36",
    "fredapi>=0.5.2",
    "confluent-kafka>=2.3.0",
    "pandas>=2.2.0",
    "numpy>=1.26.0",
    "scikit-learn>=1.4.0",
    "xgboost>=2.0.0",
    "optuna>=3.5.0",
    "transformers>=4.37.0",
    "torch>=2.2.0",
    "fastapi>=0.109.0",
    "uvicorn[standard]>=0.27.0",
    "pydantic>=2.6.0",
    "pydantic-settings>=2.1.0",
    "redis>=5.0.0",
    "apache-airflow>=2.8.0",
    "python-dotenv>=1.0.0",
    "httpx>=0.26.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-cov>=4.1.0",
    "pytest-asyncio>=0.23.0",
    "ruff>=0.2.0",
    "mypy>=1.8.0",
    "types-redis>=4.6.0",
    "pandas-stubs>=2.1.4",
]

[tool.hatch.build.targets.wheel]
packages = ["src"]

[tool.ruff]
target-version = "py312"
line-length = 99

[tool.ruff.lint]
select = ["E","W","F","I","N","UP","B","SIM","TCH","RUF"]
ignore = ["E501","B008"]

[tool.ruff.lint.isort]
known-first-party = ["src"]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"

[tool.mypy]
python_version = "3.12"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
plugins = ["pydantic.mypy"]

[[tool.mypy.overrides]]
module = ["yfinance.*","fredapi.*","confluent_kafka.*","airflow.*","xgboost.*","optuna.*","transformers.*"]
ignore_missing_imports = true

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
asyncio_mode = "auto"
addopts = "-v --tb=short --strict-markers"
markers = [
    "integration: marks tests as integration tests",
    "slow: marks tests as slow",
]
'@ | Set-Content (Join-Path $root "backend/pyproject.toml") -Encoding UTF8

# ── backend/alembic.ini ──
@'
[alembic]
script_location = alembic
prepend_sys_path = .
sqlalchemy.url = postgresql+psycopg2://finsense:finsense_secret@localhost:5432/finsense

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARNING
handlers = console
qualname =

[logger_sqlalchemy]
level = WARNING
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
'@ | Set-Content (Join-Path $root "backend/alembic.ini") -Encoding UTF8

# ── backend/alembic/env.py ──
@'
"""Alembic environment configuration."""

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool

from src.database import Base
from src.models import ModelRegistry, Prediction, RawPrice, TechnicalIndicator  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

database_url = os.environ.get("DATABASE_URL_SYNC")
if database_url:
    config.set_main_option("sqlalchemy.url", database_url)


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = create_engine(
        config.get_main_option("sqlalchemy.url", ""),
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
'@ | Set-Content (Join-Path $root "backend/alembic/env.py") -Encoding UTF8

# ── backend/alembic/script.py.mako ──
@'
"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

revision: str = ${repr(up_revision)}
down_revision: Union[str, None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
'@ | Set-Content (Join-Path $root "backend/alembic/script.py.mako") -Encoding UTF8

# ── backend/alembic/versions/001_initial_schema.py ──
@'
"""initial schema with all four tables

Revision ID: 001_initial
Revises:
Create Date: 2025-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS timescaledb")

    op.create_table(
        "raw_prices",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("ticker", sa.String(length=10), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("open", sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column("high", sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column("low", sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column("close", sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column("volume", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_raw_prices")),
    )
    op.create_index("ix_raw_prices_ticker", "raw_prices", ["ticker"])
    op.create_index("ix_raw_prices_ticker_timestamp", "raw_prices", ["ticker", "timestamp"], unique=True)
    op.execute("SELECT create_hypertable('raw_prices', 'timestamp', migrate_data => true, if_not_exists => true)")

    op.create_table(
        "technical_indicators",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("ticker", sa.String(length=10), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("rsi_14", sa.Numeric(precision=8, scale=4), nullable=True),
        sa.Column("macd", sa.Numeric(precision=12, scale=6), nullable=True),
        sa.Column("macd_signal", sa.Numeric(precision=12, scale=6), nullable=True),
        sa.Column("bollinger_upper", sa.Numeric(precision=12, scale=4), nullable=True),
        sa.Column("bollinger_lower", sa.Numeric(precision=12, scale=4), nullable=True),
        sa.Column("sma_50", sa.Numeric(precision=12, scale=4), nullable=True),
        sa.Column("sma_200", sa.Numeric(precision=12, scale=4), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_technical_indicators")),
    )
    op.create_index("ix_technical_indicators_ticker", "technical_indicators", ["ticker"])
    op.create_index("ix_technical_indicators_ticker_timestamp", "technical_indicators", ["ticker", "timestamp"], unique=True)

    op.create_table(
        "predictions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("ticker", sa.String(length=10), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("predicted_direction", sa.String(length=4), nullable=False),
        sa.Column("confidence", sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column("model_version", sa.String(length=50), nullable=False),
        sa.Column("actual_direction", sa.String(length=4), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_predictions")),
    )
    op.create_index("ix_predictions_ticker", "predictions", ["ticker"])
    op.create_index("ix_predictions_ticker_timestamp", "predictions", ["ticker", "timestamp"])

    op.create_table(
        "model_registry",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("model_name", sa.String(length=100), nullable=False),
        sa.Column("version", sa.String(length=50), nullable=False),
        sa.Column("accuracy", sa.Numeric(precision=6, scale=4), nullable=False),
        sa.Column("precision_score", sa.Numeric(precision=6, scale=4), nullable=False),
        sa.Column("recall", sa.Numeric(precision=6, scale=4), nullable=False),
        sa.Column("f1", sa.Numeric(precision=6, scale=4), nullable=False),
        sa.Column("trained_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("model_path", sa.String(length=500), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_model_registry")),
        sa.UniqueConstraint("version", name=op.f("uq_model_registry_version")),
    )
    op.create_index("ix_model_registry_is_active", "model_registry", ["is_active"])


def downgrade() -> None:
    op.drop_table("model_registry")
    op.drop_table("predictions")
    op.drop_table("technical_indicators")
    op.drop_table("raw_prices")
'@ | Set-Content (Join-Path $root "backend/alembic/versions/001_initial_schema.py") -Encoding UTF8

# ── backend/src/config.py ──
@'
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
    model_artifacts_path: str = "./models"
    environment: str = "development"
    log_level: str = "INFO"


settings = Settings()
'@ | Set-Content (Join-Path $root "backend/src/config.py") -Encoding UTF8

# ── backend/src/database.py ──
@'
"""SQLAlchemy engine, session factory, and base model."""

from collections.abc import AsyncGenerator

from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from src.config import settings

NAMING_CONVENTION: dict[str, str] = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


engine = create_async_engine(
    settings.database_url,
    echo=settings.environment == "development",
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
)

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that yields an async database session."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
'@ | Set-Content (Join-Path $root "backend/src/database.py") -Encoding UTF8

# ── backend/src/models/__init__.py ──
@'
"""SQLAlchemy ORM models for FinSense."""

from src.models.model_registry import ModelRegistry
from src.models.predictions import Prediction
from src.models.raw_prices import RawPrice
from src.models.technical_indicators import TechnicalIndicator

__all__ = ["ModelRegistry", "Prediction", "RawPrice", "TechnicalIndicator"]
'@ | Set-Content (Join-Path $root "backend/src/models/__init__.py") -Encoding UTF8

# ── backend/src/models/raw_prices.py ──
@'
"""ORM model for raw stock price data (OHLCV)."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, DateTime, Index, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base


class RawPrice(Base):
    """Raw OHLCV stock price data. TimescaleDB hypertable on timestamp."""

    __tablename__ = "raw_prices"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    open: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    high: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    low: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    close: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    volume: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
    )

    __table_args__ = (
        Index("ix_raw_prices_ticker_timestamp", "ticker", "timestamp", unique=True),
    )

    def __repr__(self) -> str:
        return f"<RawPrice(ticker={self.ticker!r}, timestamp={self.timestamp}, close={self.close})>"
'@ | Set-Content (Join-Path $root "backend/src/models/raw_prices.py") -Encoding UTF8

# ── backend/src/models/technical_indicators.py ──
@'
"""ORM model for computed technical indicators."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Index, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base


class TechnicalIndicator(Base):
    """Computed technical indicators for each ticker at each timestamp."""

    __tablename__ = "technical_indicators"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    rsi_14: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), nullable=True)
    macd: Mapped[Decimal | None] = mapped_column(Numeric(12, 6), nullable=True)
    macd_signal: Mapped[Decimal | None] = mapped_column(Numeric(12, 6), nullable=True)
    bollinger_upper: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    bollinger_lower: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    sma_50: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    sma_200: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
    )

    __table_args__ = (
        Index("ix_technical_indicators_ticker_timestamp", "ticker", "timestamp", unique=True),
    )

    def __repr__(self) -> str:
        return f"<TechnicalIndicator(ticker={self.ticker!r}, timestamp={self.timestamp}, rsi_14={self.rsi_14})>"
'@ | Set-Content (Join-Path $root "backend/src/models/technical_indicators.py") -Encoding UTF8

# ── backend/src/models/predictions.py ──
@'
"""ORM model for ML model predictions."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Index, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base


class Prediction(Base):
    """ML model predictions for stock price direction."""

    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    predicted_direction: Mapped[str] = mapped_column(String(4), nullable=False)
    confidence: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    model_version: Mapped[str] = mapped_column(String(50), nullable=False)
    actual_direction: Mapped[str | None] = mapped_column(String(4), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
    )

    __table_args__ = (
        Index("ix_predictions_ticker_timestamp", "ticker", "timestamp"),
    )

    def __repr__(self) -> str:
        return f"<Prediction(ticker={self.ticker!r}, predicted={self.predicted_direction}, confidence={self.confidence})>"
'@ | Set-Content (Join-Path $root "backend/src/models/predictions.py") -Encoding UTF8

# ── backend/src/models/model_registry.py ──
@'
"""ORM model for ML model versioning and registry."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, Index, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base


class ModelRegistry(Base):
    """Registry of trained ML models with performance metrics."""

    __tablename__ = "model_registry"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    version: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    accuracy: Mapped[Decimal] = mapped_column(Numeric(6, 4), nullable=False)
    precision_score: Mapped[Decimal] = mapped_column(Numeric(6, 4), nullable=False)
    recall: Mapped[Decimal] = mapped_column(Numeric(6, 4), nullable=False)
    f1: Mapped[Decimal] = mapped_column(Numeric(6, 4), nullable=False)
    trained_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    model_path: Mapped[str] = mapped_column(String(500), nullable=False)

    __table_args__ = (
        Index("ix_model_registry_is_active", "is_active"),
    )

    def __repr__(self) -> str:
        return f"<ModelRegistry(name={self.model_name!r}, version={self.version!r}, f1={self.f1}, active={self.is_active})>"
'@ | Set-Content (Join-Path $root "backend/src/models/model_registry.py") -Encoding UTF8

# ── backend/tests/conftest.py ──
@'
"""Shared test fixtures for the FinSense test suite."""

import pytest


@pytest.fixture
def sample_tickers() -> list[str]:
    """Return the list of tracked tickers."""
    return [
        "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA",
        "META", "TSLA", "JPM", "V", "JNJ",
        "WMT", "PG", "DIS", "NFLX", "AMD",
    ]
'@ | Set-Content (Join-Path $root "backend/tests/conftest.py") -Encoding UTF8

Write-Host ""
Write-Host "Phase 1 setup complete!" -ForegroundColor Green
Write-Host "Files created in: $root" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  cd backend"
Write-Host "  pip install -e '.[dev]'"
Write-Host "  alembic upgrade head"
