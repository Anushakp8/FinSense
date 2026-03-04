"""Model registry for versioning and model management.

Provides CRUD operations for the model_registry table, including
model registration, promotion, and retrieval of the active model.
"""

import logging
import pickle
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)

# Auto-promote threshold: new model must beat current by this much (F1)
AUTO_PROMOTE_THRESHOLD = 0.01


def register_model(
    engine: Engine,
    model_name: str,
    version: str,
    metrics: dict[str, float],
    model_path: str,
) -> int:
    """Register a trained model in the registry.

    Args:
        engine: SQLAlchemy sync engine.
        model_name: Name of the model (e.g., "xgboost").
        version: Version string (e.g., "20240102_153000").
        metrics: Dict with accuracy, precision, recall, f1 keys.
        model_path: File path to the saved model pickle.

    Returns:
        The ID of the registered model.
    """
    insert_sql = text("""
        INSERT INTO model_registry
            (model_name, version, accuracy, precision_score, recall, f1,
             trained_at, is_active, model_path)
        VALUES
            (:model_name, :version, :accuracy, :precision_score, :recall, :f1,
             :trained_at, :is_active, :model_path)
        RETURNING id
    """)

    params = {
        "model_name": model_name,
        "version": version,
        "accuracy": metrics["accuracy"],
        "precision_score": metrics["precision"],
        "recall": metrics["recall"],
        "f1": metrics["f1"],
        "trained_at": datetime.now(timezone.utc),
        "is_active": False,
        "model_path": model_path,
    }

    with engine.begin() as conn:
        result = conn.execute(insert_sql, params)
        model_id = result.scalar()

    logger.info(
        "Registered model: %s v%s (id=%d, F1=%.4f)",
        model_name, version, model_id, metrics["f1"],
    )
    return model_id


def get_active_model(engine: Engine) -> tuple[object, dict[str, object]] | None:
    """Load the currently active model and its metadata.

    Args:
        engine: SQLAlchemy sync engine.

    Returns:
        Tuple of (model_object, metadata_dict) or None if no active model.
    """
    query = text("""
        SELECT id, model_name, version, accuracy, precision_score,
               recall, f1, trained_at, model_path
        FROM model_registry
        WHERE is_active = TRUE
        LIMIT 1
    """)

    with engine.connect() as conn:
        result = conn.execute(query)
        row = result.fetchone()

    if row is None:
        logger.warning("No active model found in registry")
        return None

    metadata = {
        "id": row[0],
        "model_name": row[1],
        "version": row[2],
        "accuracy": float(row[3]) if isinstance(row[3], Decimal) else row[3],
        "precision": float(row[4]) if isinstance(row[4], Decimal) else row[4],
        "recall": float(row[5]) if isinstance(row[5], Decimal) else row[5],
        "f1": float(row[6]) if isinstance(row[6], Decimal) else row[6],
        "trained_at": row[7],
        "model_path": row[8],
    }

    try:
        with open(metadata["model_path"], "rb") as f:
            model = pickle.load(f)  # noqa: S301
    except FileNotFoundError:
        logger.error("Model file not found: %s", metadata["model_path"])
        return None

    logger.info(
        "Loaded active model: %s v%s (F1=%.4f)",
        metadata["model_name"], metadata["version"], metadata["f1"],
    )
    return model, metadata


def promote_model(engine: Engine, version: str) -> bool:
    """Promote a model version to active, deactivating all others.

    Args:
        engine: SQLAlchemy sync engine.
        version: Version string to promote.

    Returns:
        True if promotion succeeded, False if version not found.
    """
    with engine.begin() as conn:
        # Deactivate all models
        conn.execute(text("UPDATE model_registry SET is_active = FALSE"))

        # Activate the specified version
        result = conn.execute(
            text("UPDATE model_registry SET is_active = TRUE WHERE version = :version"),
            {"version": version},
        )

        if result.rowcount == 0:
            logger.error("Model version %s not found", version)
            return False

    logger.info("Promoted model version %s to active", version)
    return True


def auto_promote_if_better(
    engine: Engine,
    new_version: str,
    new_f1: float,
    threshold: float = AUTO_PROMOTE_THRESHOLD,
) -> bool:
    """Auto-promote a new model if it beats the current active model.

    Args:
        engine: SQLAlchemy sync engine.
        new_version: Version of the new model.
        new_f1: F1 score of the new model.
        threshold: Minimum improvement required for promotion.

    Returns:
        True if the new model was promoted.
    """
    # Check current active model's F1
    query = text("SELECT version, f1 FROM model_registry WHERE is_active = TRUE LIMIT 1")
    with engine.connect() as conn:
        result = conn.execute(query)
        row = result.fetchone()

    if row is None:
        # No active model â€” promote the new one
        logger.info("No active model found, promoting %s", new_version)
        return promote_model(engine, new_version)

    current_f1 = float(row[1]) if isinstance(row[1], Decimal) else row[1]
    improvement = new_f1 - current_f1

    if improvement > threshold:
        logger.info(
            "New model (F1=%.4f) beats current (F1=%.4f) by %.4f (threshold=%.4f). Promoting.",
            new_f1, current_f1, improvement, threshold,
        )
        return promote_model(engine, new_version)

    logger.info(
        "New model (F1=%.4f) does not beat current (F1=%.4f) by enough (%.4f < %.4f). Keeping current.",
        new_f1, current_f1, improvement, threshold,
    )
    return False


def list_models(engine: Engine) -> list[dict[str, object]]:
    """List all models in the registry.

    Args:
        engine: SQLAlchemy sync engine.

    Returns:
        List of model metadata dicts.
    """
    query = text("""
        SELECT id, model_name, version, accuracy, precision_score,
               recall, f1, trained_at, is_active, model_path
        FROM model_registry
        ORDER BY trained_at DESC
    """)

    with engine.connect() as conn:
        result = conn.execute(query)
        rows = result.fetchall()

    return [
        {
            "id": row[0],
            "model_name": row[1],
            "version": row[2],
            "accuracy": float(row[3]),
            "precision": float(row[4]),
            "recall": float(row[5]),
            "f1": float(row[6]),
            "trained_at": row[7],
            "is_active": row[8],
            "model_path": row[9],
        }
        for row in rows
    ]
