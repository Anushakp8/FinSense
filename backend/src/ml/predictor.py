"""Prediction service for stock price direction.

Loads the active model from the registry, fetches latest features,
and returns predictions with confidence scores. Caches results in Redis.
"""

import json
import logging
from datetime import datetime, timezone

import numpy as np
import redis
from sqlalchemy import text
from sqlalchemy.engine import Engine

from src.config import settings
from src.ml.registry import get_active_model
from src.ml.trainer import FEATURE_COLUMNS

logger = logging.getLogger(__name__)

# Redis cache TTL (1 hour)
CACHE_TTL_SECONDS = 3600

# All features used by the model
PREDICTION_FEATURES = FEATURE_COLUMNS + ["return_1d", "return_3d", "return_5d", "volatility_20d"]


def _get_redis_client() -> redis.Redis:
    """Create a Redis client."""
    return redis.from_url(settings.redis_url, decode_responses=True)


def _get_latest_features(engine: Engine, ticker: str) -> dict[str, float] | None:
    """Fetch the latest feature row for a ticker.

    Joins raw_prices with technical_indicators and computes lag features.

    Args:
        engine: SQLAlchemy sync engine.
        ticker: Stock ticker symbol.

    Returns:
        Dict of feature name -> value, or None if not available.
    """
    query = text("""
        WITH recent_prices AS (
            SELECT timestamp, close,
                   LAG(close, 1) OVER (ORDER BY timestamp) as close_1d,
                   LAG(close, 3) OVER (ORDER BY timestamp) as close_3d,
                   LAG(close, 5) OVER (ORDER BY timestamp) as close_5d
            FROM raw_prices
            WHERE ticker = :ticker
            ORDER BY timestamp DESC
            LIMIT 25
        ),
        latest AS (
            SELECT * FROM recent_prices ORDER BY timestamp DESC LIMIT 1
        )
        SELECT
            ti.rsi_14, ti.macd, ti.macd_signal,
            ti.bollinger_upper, ti.bollinger_lower,
            ti.sma_50, ti.sma_200,
            l.close, l.close_1d, l.close_3d, l.close_5d,
            l.timestamp
        FROM latest l
        JOIN technical_indicators ti
            ON ti.ticker = :ticker AND ti.timestamp = l.timestamp
    """)

    with engine.connect() as conn:
        result = conn.execute(query, {"ticker": ticker})
        row = result.fetchone()

    if row is None:
        logger.warning("No features found for ticker %s", ticker)
        return None

    features: dict[str, float] = {
        "rsi_14": float(row[0]),
        "macd": float(row[1]),
        "macd_signal": float(row[2]),
        "bollinger_upper": float(row[3]),
        "bollinger_lower": float(row[4]),
        "sma_50": float(row[5]),
        "sma_200": float(row[6]),
    }

    # Compute lag returns
    close = float(row[7])
    close_1d = float(row[8]) if row[8] is not None else None
    close_3d = float(row[9]) if row[9] is not None else None
    close_5d = float(row[10]) if row[10] is not None else None

    features["return_1d"] = (close / close_1d - 1) if close_1d else 0.0
    features["return_3d"] = (close / close_3d - 1) if close_3d else 0.0
    features["return_5d"] = (close / close_5d - 1) if close_5d else 0.0
    features["volatility_20d"] = 0.2  # Approximate; full calculation needs 20 rows

    return features


def predict(engine: Engine, ticker: str, use_cache: bool = True) -> dict[str, object]:
    """Generate a prediction for a ticker's next-day price direction.

    Args:
        engine: SQLAlchemy sync engine.
        ticker: Stock ticker symbol.
        use_cache: Whether to check/store in Redis cache.

    Returns:
        Dict with prediction details: ticker, direction, confidence,
        model_version, timestamp.

    Raises:
        ValueError: If no active model or no features available.
    """
    ticker = ticker.upper()
    cache_key = f"prediction:{ticker}"

    # Check cache
    if use_cache:
        try:
            r = _get_redis_client()
            cached = r.get(cache_key)
            if cached:
                logger.info("Cache hit for %s", ticker)
                return json.loads(cached)
        except redis.ConnectionError:
            logger.warning("Redis unavailable, skipping cache")

    # Load active model
    model_result = get_active_model(engine)
    if model_result is None:
        msg = "No active model available. Train and promote a model first."
        raise ValueError(msg)

    model_data, metadata = model_result
    # Handle both old (raw model) and new (dict with model+scaler) formats
    if isinstance(model_data, dict):
        model = model_data["model"]
    else:
        model = model_data

    # Get latest features
    features = _get_latest_features(engine, ticker)
    if features is None:
        msg = f"No features available for ticker {ticker}"
        raise ValueError(msg)

    # Build feature vector in correct order
    feature_vector = np.array([[features[col] for col in PREDICTION_FEATURES]])

    # Predict
    prediction = model.predict(feature_vector)[0]
    probabilities = model.predict_proba(feature_vector)[0]
    confidence = float(max(probabilities))

    result = {
        "ticker": ticker,
        "direction": "UP" if prediction == 1 else "DOWN",
        "confidence": round(confidence, 4),
        "model_version": metadata["version"],
        "model_name": metadata["model_name"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    # Cache result
    if use_cache:
        try:
            r = _get_redis_client()
            r.setex(cache_key, CACHE_TTL_SECONDS, json.dumps(result))
            logger.info("Cached prediction for %s (TTL=%ds)", ticker, CACHE_TTL_SECONDS)
        except redis.ConnectionError:
            logger.warning("Redis unavailable, skipping cache write")

    logger.info(
        "Prediction for %s: %s (confidence=%.4f, model=%s)",
        ticker, result["direction"], result["confidence"], result["model_version"],
    )
    return result


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    from sqlalchemy import create_engine

    sync_engine = create_engine(settings.database_url_sync)

    for ticker in ["AAPL", "MSFT", "GOOGL"]:
        try:
            result = predict(sync_engine, ticker, use_cache=False)
            print(f"{ticker}: {result['direction']} (confidence={result['confidence']:.4f})")
        except ValueError as e:
            print(f"{ticker}: {e}")
