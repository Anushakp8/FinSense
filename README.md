# FinSense â€” Real-Time Financial Data Pipeline with ML Predictions

An end-to-end financial data engineering project that ingests real-time stock and economic data, transforms it through a structured pipeline, trains ML models for price movement prediction, and serves predictions through a FastAPI backend with a professional Next.js dashboard.

## Architecture

```mermaid
graph TB
    subgraph Data Sources
        YF[Yahoo Finance API]
        FRED[FRED API]
    end

    subgraph Ingestion Layer
        SF[Stock Fetcher]
        EF[Economic Fetcher]
        KP[Kafka Producer]
        KC[Kafka Consumer]
    end

    subgraph Infrastructure
        PG[(PostgreSQL + TimescaleDB)]
        RD[(Redis Cache)]
        KF[Apache Kafka]
        AF[Apache Airflow]
    end

    subgraph Feature Engineering
        TI[Technical Indicators]
        LF[Lag Features]
        VOL[Volatility]
    end

    subgraph ML Pipeline
        EDA[EDA & Data Quality]
        DP[Data Preparation]
        TR[Model Training]
        MR[Model Registry]
        PR[Predictor]
    end

    subgraph API Layer
        FA[FastAPI Backend]
        EP1[/stocks]
        EP2[/predict]
        EP3[/portfolio-risk]
        EP4[/pipeline-status]
    end

    subgraph Frontend
        NX[Next.js 15 Dashboard]
        DB[Dashboard Page]
        PD[Predictions Page]
        PF[Portfolio Page]
        PL[Pipeline Page]
    end

    YF --> SF --> PG
    FRED --> EF --> PG
    SF --> KP --> KF --> KC --> PG
    AF --> SF & TI & TR
    PG --> TI & LF & VOL --> PG
    PG --> EDA --> DP --> TR --> MR
    MR --> PR --> RD
    PG --> FA
    RD --> FA
    FA --> EP1 & EP2 & EP3 & EP4
    EP1 & EP2 & EP3 & EP4 --> NX
    NX --> DB & PD & PF & PL
```

## Tech Stack

**Backend**: Python 3.12, PostgreSQL 16 + TimescaleDB, Apache Kafka, Apache Airflow, FastAPI, Redis, scikit-learn, XGBoost, Optuna

**Frontend**: Next.js 15, TypeScript (strict), Material UI v6, TanStack Query v5, Recharts

**Infrastructure**: Docker Compose, GitHub Actions

## Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/Anushakp8/FinSense.git
cd finsense

# 2. Copy environment variables
cp .env.example .env
# Edit .env with your FRED API key

# 3. Start infrastructure
docker compose up -d

# 4. Set up Python environment
cd backend
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1  # Windows
pip install -e ".[dev]"

# 5. Run database migrations
alembic upgrade head

# 6. Ingest data and compute features
python -m src.ingestion.stock_fetcher
python -m src.features.pipeline

# 7. Train ML model
python -m src.ml.trainer

# 8. Start API server
uvicorn src.api.main:app --reload --port 8000

# 9. Start frontend (new terminal)
cd frontend
bun install
bun run dev
```

Open http://localhost:3000 for the dashboard, http://localhost:8000/docs for API docs.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /health | API health check |
| GET | /api/v1/stocks | List all tracked tickers with latest prices |
| GET | /api/v1/stocks/{ticker} | Detailed stock data with technical indicators |
| GET | /api/v1/stocks/{ticker}/history | Historical OHLCV data (paginated) |
| POST | /api/v1/predict | ML prediction for next-day price direction |
| GET | /api/v1/portfolio-risk | Portfolio VaR, Sharpe ratio, max drawdown |
| GET | /api/v1/pipeline-status | Pipeline health, data freshness, model status |

## ML Model Performance

**Model**: XGBoost classifier with walk-forward validation (520 folds)

| Metric | Value |
|--------|-------|
| Accuracy | 50.7% |
| Precision | 51.9% |
| Recall | 51.3% |
| F1 Score | 45.5% |
| AUC-ROC | 55.0% |

**Data Preparation Pipeline**:
- EDA report (missing values, duplicates, class balance, correlations, outliers)
- IQR outlier capping per fold
- StandardScaler normalization (fit on train, transform test)
- Walk-forward validation (252-day train / 21-day test windows)

## Model Limitations

### Expected Accuracy
The model achieves ~51% accuracy across 520 walk-forward validation folds, which is realistic for stock direction prediction. Financial markets are highly efficient, and consistently predicting direction above 55% with technical indicators alone is extremely difficult.

### Important Disclaimers
- **Past performance does not predict future results.** This is a portfolio project demonstrating data engineering and ML skills, not financial advice.
- The model uses only technical indicators (RSI, MACD, Bollinger Bands, SMAs) and lag features. Fundamental analysis, sentiment data, and macroeconomic factors are not incorporated.
- Walk-forward validation prevents data leakage, but real-world deployment faces additional challenges (transaction costs, slippage, regime changes).

### Potential Improvements
- **Alternative data**: News sentiment (FinBERT), social media signals, options flow
- **Deeper NLP**: Fine-tuned language models on financial filings and earnings calls
- **Ensemble methods**: Stacking multiple model types with meta-learners
- **Feature expansion**: Sector rotation signals, cross-asset correlations, volatility surface features
- **Longer training windows**: Expanding beyond 252 days with adaptive weighting for recent data

## Tracked Tickers

AAPL, MSFT, GOOGL, AMZN, NVDA, META, TSLA, JPM, V, JNJ, WMT, PG, DIS, NFLX, AMD

## Project Status

- [x] Phase 1: Project Scaffolding and Infrastructure
- [x] Phase 2: Data Ingestion Pipeline
- [x] Phase 3: Feature Engineering Pipeline (v0.1.0)
- [x] Phase 4: Airflow Orchestration
- [x] Phase 5: ML Model Training with EDA and Data Prep
- [x] Phase 6: FastAPI Backend (v0.5.0)
- [x] Phase 7: Frontend Dashboard â€” Setup and Layout
- [x] Phase 8: Frontend Dashboard â€” Pages and Data Integration
- [x] Phase 9: Integration Testing, Polish, and Documentation
- [x] Phase 10: Backtest Report and Final Commit (v1.0.0)

## License

MIT
