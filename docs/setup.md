# FinSense â€” Local Development Setup Guide

## Prerequisites

- **Python 3.12** â€” [Download](https://www.python.org/downloads/)
- **Docker Desktop** â€” [Download](https://www.docker.com/products/docker-desktop/) (AMD64 for Intel/AMD)
- **Bun** â€” Install: `powershell -c "irm bun.sh/install.ps1 | iex"`
- **Git** â€” [Download](https://git-scm.com/downloads)

## Step 1: Clone and Configure

```bash
git clone https://github.com/Anushakp8/FinSense.git
cd finsense
cp .env.example .env
```

Edit `.env` and set your FRED API key (get free at https://fred.stlouisfed.org/docs/api/api_key.html).

## Step 2: Start Infrastructure

```bash
docker compose up -d
```

Wait for all services to be healthy:
```bash
docker compose ps
```

Expected: PostgreSQL, Redis, Kafka, Zookeeper, Airflow (webserver + scheduler) all running.

## Step 3: Backend Setup

```bash
cd backend
py -3.12 -m venv .venv

# Windows:
.venv\Scripts\Activate.ps1
# If blocked: Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned

pip install -e ".[dev]"
```

## Step 4: Database Migration

```bash
alembic upgrade head
```

## Step 5: Data Ingestion

```bash
# Fetch historical stock data (all available history)
python -m src.ingestion.stock_fetcher

# Compute technical indicators
python -m src.features.pipeline
```

## Step 6: Train ML Model

```bash
python -m src.ml.trainer
```

This runs EDA, data preparation, and walk-forward validation with Optuna tuning. Takes 30-60 minutes with full history.

After training, register and promote the model (update version string from training output):
```python
python -c "
from sqlalchemy import create_engine
from src.config import settings
from src.ml.registry import register_model, promote_model

engine = create_engine(settings.database_url_sync)
register_model(engine, 'xgboost', 'YOUR_VERSION', {'accuracy': 0.51, 'precision': 0.52, 'recall': 0.51, 'f1': 0.46}, './models/YOUR_MODEL_FILE.pkl')
promote_model(engine, 'YOUR_VERSION')
"
```

## Step 7: Start API Server

```bash
uvicorn src.api.main:app --reload --port 8000
```

Verify: http://localhost:8000/docs

## Step 8: Start Frontend

```bash
cd frontend
bun install
bun run dev
```

Open: http://localhost:3000

## Troubleshooting

- **Docker: `docker compose` not found** â€” Use modern Docker Desktop (no hyphen)
- **Python: package conflicts** â€” Use Python 3.12 in a venv, not 3.14
- **Airflow: database "airflow" not found** â€” Run `docker exec finsense-postgres psql -U finsense -d finsense -c "CREATE DATABASE airflow;"`
- **Kafka: cluster ID mismatch** â€” Run `docker compose down && docker volume rm finsense_kafka_data finsense_zookeeper_data && docker compose up -d`
- **Frontend: Turbopack panics** â€” Use Next.js 15 (not 16) which doesn't force Turbopack
