"""FinSense Daily Pipeline DAG.

Orchestrates the full data pipeline: ingest â†’ validate â†’ compute features.
Model training and serving tasks are placeholder stubs until Phase 5.

Schedule: 6 PM EST on weekdays (after market close).
"""

import logging
import os
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

logger = logging.getLogger(__name__)

# Default args applied to all tasks
DEFAULT_ARGS = {
    "owner": "finsense",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

# Database URL from environment (set in docker-compose.yml)
DATABASE_URL_SYNC = os.environ.get(
    "FINSENSE_DB_URL",
    "postgresql+psycopg2://finsense:finsense_secret@localhost:5432/finsense",
)


def _get_engine():
    """Create a SQLAlchemy sync engine."""
    from sqlalchemy import create_engine
    return create_engine(DATABASE_URL_SYNC)


def task_ingest_data(**kwargs):
    """Task 1: Fetch latest stock data for all tickers.

    Pulls the most recent data (1 month) to catch up on any missing days.
    ON CONFLICT DO NOTHING ensures no duplicates.
    """
    import sys
    sys.path.insert(0, "/opt/airflow/src")

    from src.ingestion.stock_fetcher import run_stock_ingestion

    engine = _get_engine()
    count = run_stock_ingestion(engine, period="1mo")
    logger.info("Ingested %d new price rows", count)
    return count


def task_validate_data(**kwargs):
    """Task 2: Run data quality checks.

    Checks null rates, data freshness, row counts, and flags outliers.
    Raises DataQualityError if any critical check fails.
    """
    import sys
    sys.path.insert(0, "/opt/airflow/src")

    from src.ingestion.data_quality import run_all_quality_checks

    engine = _get_engine()
    results = run_all_quality_checks(engine)
    logger.info("Data quality check results: %s", results)
    return results


def task_compute_features(**kwargs):
    """Task 3: Run the feature engineering pipeline.

    Computes technical indicators for all tickers and inserts
    into the technical_indicators table.
    """
    import sys
    sys.path.insert(0, "/opt/airflow/src")

    from src.features.pipeline import run_feature_pipeline

    engine = _get_engine()
    results = run_feature_pipeline(engine)
    total = sum(results.values())
    logger.info("Computed features: %d total rows for %d tickers", total, len(results))
    return results


def task_train_model(**kwargs):
    """Task 4: Trigger model retraining.

    Placeholder â€” will be implemented in Phase 5.
    """
    logger.info("Model training placeholder â€” will be implemented in Phase 5")
    return {"status": "placeholder", "message": "Awaiting Phase 5 implementation"}


def task_serve_model(**kwargs):
    """Task 5: Register and activate the new model.

    Placeholder â€” will be implemented in Phase 5.
    """
    logger.info("Model serving placeholder â€” will be implemented in Phase 5")
    return {"status": "placeholder", "message": "Awaiting Phase 5 implementation"}


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# DAG Definition
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
with DAG(
    dag_id="finsense_daily_pipeline",
    default_args=DEFAULT_ARGS,
    description="Daily pipeline: ingest stock data, validate, compute features, train/serve model",
    schedule="0 18 * * 1-5",  # 6 PM EST on weekdays (after market close)
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["finsense", "daily", "pipeline"],
    max_active_runs=1,
) as dag:

    ingest = PythonOperator(
        task_id="ingest_data",
        python_callable=task_ingest_data,
    )

    validate = PythonOperator(
        task_id="validate_data",
        python_callable=task_validate_data,
    )

    features = PythonOperator(
        task_id="compute_features",
        python_callable=task_compute_features,
    )

    train = PythonOperator(
        task_id="train_model",
        python_callable=task_train_model,
    )

    serve = PythonOperator(
        task_id="serve_model",
        python_callable=task_serve_model,
    )

    # Define task dependencies
    ingest >> validate >> features >> train >> serve
