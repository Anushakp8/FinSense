# FinSense System Architecture

## Overview

FinSense follows a layered architecture with clear separation between data ingestion, feature engineering, ML training, API serving, and frontend presentation.

## Data Flow

```
Yahoo Finance / FRED API
        |
        v
  [Ingestion Layer]
  - stock_fetcher.py (batch historical data)
  - economic_fetcher.py (macro indicators)
  - kafka_producer.py (simulated real-time streaming)
  - kafka_consumer.py (stream consumption)
        |
        v
  [PostgreSQL + TimescaleDB]
  - raw_prices (hypertable, 143K+ rows)
  - technical_indicators (136K+ rows)
  - economic_indicators
  - predictions
  - model_registry
        |
        v
  [Feature Engineering]
  - RSI-14, MACD, Bollinger Bands, SMA-50, SMA-200
  - Lag returns (1, 3, 5 day)
  - Rolling volatility (20-day annualized)
        |
        v
  [ML Pipeline]
  - EDA & data quality checks
  - Data preparation (scaling, outlier capping, imputation)
  - Walk-forward validation (252/21 day windows)
  - 3 models: Logistic Regression, Random Forest, XGBoost
  - Optuna hyperparameter tuning (50 trials per fold)
  - Model registry with auto-promotion
        |
        v
  [FastAPI Backend]
  - 6 REST endpoints
  - Redis caching for predictions
  - CORS middleware for frontend
        |
        v
  [Next.js Frontend]
  - Material UI dark theme ("FinSense Midnight")
  - TanStack Query for data fetching
  - Recharts for visualizations
  - 4 pages: Dashboard, Predictions, Portfolio, Pipeline
```

## Database Schema

| Table | Rows | Description |
|-------|------|-------------|
| raw_prices | 143,907 | OHLCV data for 15 tickers (TimescaleDB hypertable) |
| technical_indicators | 136,392 | RSI, MACD, Bollinger, SMAs per ticker/date |
| economic_indicators | Variable | GDP, CPI, unemployment, fed funds, 10Y treasury |
| predictions | Variable | ML predictions with confidence scores |
| model_registry | Variable | Trained model versions with metrics |

## Infrastructure

All services run via Docker Compose:
- PostgreSQL 16 + TimescaleDB
- Redis 7 (caching)
- Apache Kafka + Zookeeper (streaming simulation)
- Apache Airflow 2.8+ (orchestration)
