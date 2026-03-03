# FinSense â€” Task Tracking

## Phase 1: Project Scaffolding and Infrastructure

**Goal**: Set up the full project structure, Docker environment, and database schema.

### Tasks

- [x] 1.1 Create the full folder structure (`finsense/` with all subdirectories and `__init__.py` files)
- [x] 1.2 Create `docker-compose.yml` with all services (PostgreSQL+TimescaleDB, Redis, Zookeeper+Kafka, Airflow webserver+scheduler) on shared `finsense-net` network
- [x] 1.3 Create `.env.example` with all required environment variables
- [x] 1.4 Create `backend/pyproject.toml` with all Python dependencies, ruff config, and mypy config
- [x] 1.5 Initialize Alembic for database migrations (alembic.ini, env.py, script.py.mako)
- [x] 1.6 Write SQLAlchemy ORM models for all four tables:
  - [x] `raw_prices` â€” id, ticker, timestamp, open, high, low, close, volume, created_at (hypertable on timestamp)
  - [x] `technical_indicators` â€” id, ticker, timestamp, rsi_14, macd, macd_signal, bollinger_upper, bollinger_lower, sma_50, sma_200, created_at
  - [x] `predictions` â€” id, ticker, timestamp, predicted_direction, confidence, model_version, actual_direction (nullable), created_at
  - [x] `model_registry` â€” id, model_name, version, accuracy, precision_score, recall, f1, trained_at, is_active, model_path
- [x] 1.7 Generate initial Alembic migration with TimescaleDB hypertable creation
- [x] 1.8 Create `tasks/lessons.md` with initial content
- [x] 1.9 Create `.gitignore` (Python, Node, Docker, env files, model artifacts)
- [x] 1.10 Create initial `README.md`
- [x] 1.11 **ARTIFACT**: Generated Mermaid ER diagram of database schema â€” approved by user

### Verification Checklist

- [ ] `docker-compose up` starts all services without errors (run locally)
- [ ] Alembic migration applies cleanly against Dockerized PostgreSQL (run locally)
- [ ] All four tables exist in PostgreSQL with correct columns and types
- [ ] TimescaleDB hypertable is created on `raw_prices`

**Note**: Docker verification must be done locally since Docker is not available in this environment.

### Git Checkpoint
```bash
git init
git add .
git commit -m "phase-1: project scaffolding, docker infra, database schema"
```

### Review

**Files created**: 31 files across the full project structure
**Key decisions**:
- Used `mapped_column` with `Mapped[]` type annotations (SQLAlchemy 2.0 style) for full type safety
- Set naming conventions on MetaData so Alembic generates deterministic constraint names
- Made technical indicator columns nullable (warmup periods produce NaN)
- Added unique constraint on `(ticker, timestamp)` for raw_prices and technical_indicators to prevent duplicates
- Used `server_default=func.now()` for all `created_at` columns (DB-side default)
- Configured connection pooling from the start (pool_size=10, max_overflow=20)
- Airflow uses LocalExecutor with its own database, sharing the same PostgreSQL instance
- init-db.sh script creates both the airflow DB and enables TimescaleDB extension
