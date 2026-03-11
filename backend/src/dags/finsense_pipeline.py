"""FinSense Daily Pipeline DAG.

Orchestrates the full data pipeline: ingest -> validate -> compute features ->
train models -> promote a serving model.

Schedule: 6 PM America/New_York on weekdays (after market close).
"""

import logging
import os
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator
import pendulum

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
MODEL_ARTIFACTS_DIR = os.environ.get("FINSENSE_MODEL_DIR", "/opt/airflow/models")
TRAIN_TICKERS = [
    t.strip().upper()
    for t in os.environ.get("FINSENSE_TRAIN_TICKERS", "AAPL,MSFT,GOOGL").split(",")
    if t.strip()
]


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
    """Task 4: Retrain models and register candidate versions.

    Trains per configured ticker and registers successful artifacts in
    model_registry as inactive candidates.
    """
    import sys

    sys.path.insert(0, "/opt/airflow/src")

    from src.ml.registry import register_model
    from src.ml.trainer import run_training_pipeline

    engine = _get_engine()
    candidates: list[dict[str, object]] = []
    failures: list[dict[str, object]] = []

    logger.info("Training models for tickers: %s", TRAIN_TICKERS)
    for ticker in TRAIN_TICKERS:
        result = run_training_pipeline(
            engine,
            ticker=ticker,
            model_dir=MODEL_ARTIFACTS_DIR,
            use_optuna=False,
            run_eda_report=False,
        )
        if result.get("status") != "success":
            failures.append({"ticker": ticker, "status": result.get("status")})
            logger.warning("Training skipped for %s: %s", ticker, result.get("status"))
            continue

        metrics = result["metrics"]
        model_id = register_model(
            engine,
            model_name=result["best_model_name"],
            version=result["version"],
            metrics=metrics,
            model_path=result["model_path"],
        )
        candidates.append(
            {
                "ticker": ticker,
                "model_id": model_id,
                "version": result["version"],
                "model_name": result["best_model_name"],
                "f1": metrics["f1"],
            }
        )

    summary = {
        "status": "success" if candidates else "no_candidates",
        "candidate_count": len(candidates),
        "candidates": candidates,
        "failures": failures,
    }
    logger.info("Training summary: %s", summary)
    return summary


def task_serve_model(**kwargs):
    """Task 5: Promote the best candidate model.

    Picks the highest-F1 candidate from the training task and promotes it only
    if it beats the current active model by the configured threshold.
    """
    import sys

    sys.path.insert(0, "/opt/airflow/src")

    from src.ml.registry import auto_promote_if_better

    ti = kwargs["ti"]
    training_summary = ti.xcom_pull(task_ids="train_model") or {}
    candidates = training_summary.get("candidates", [])

    if not candidates:
        logger.warning("No candidate models available for promotion")
        return {
            "status": "skipped",
            "reason": "no_candidates",
            "message": "No successful training runs produced candidate models",
        }

    best_candidate = max(candidates, key=lambda c: float(c["f1"]))
    engine = _get_engine()
    promoted = auto_promote_if_better(
        engine,
        new_version=str(best_candidate["version"]),
        new_f1=float(best_candidate["f1"]),
    )

    result = {
        "status": "promoted" if promoted else "kept_current",
        "candidate_version": best_candidate["version"],
        "candidate_model_name": best_candidate["model_name"],
        "candidate_f1": best_candidate["f1"],
    }
    logger.info("Serving decision: %s", result)
    return result


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# DAG Definition
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
with DAG(
    dag_id="finsense_daily_pipeline",
    default_args=DEFAULT_ARGS,
    description="Daily pipeline: ingest stock data, validate, compute features, train/serve model",
    schedule="0 18 * * 1-5",  # 6 PM America/New_York on weekdays
    start_date=datetime(2024, 1, 1, tzinfo=pendulum.timezone("America/New_York")),
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
