# FinSense â€” Real-Time Financial Data Pipeline with ML Predictions

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
- [ ] Phase 7: Frontend Dashboard â€” Setup and Layout
- [ ] Phase 8: Frontend Dashboard â€” Pages and Data Integration
- [ ] Phase 9: Integration Testing, Polish, and Documentation
- [ ] Phase 10: Backtest Report and Final Commit
