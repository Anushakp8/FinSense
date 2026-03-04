"""Feature engineering pipeline orchestrator.

Reads raw prices from the database, computes all technical indicators
and lag features, aligns them by timestamp, and inserts the results
into the technical_indicators table.
"""

import logging

import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine

from src.features.lag_features import compute_lag_returns, compute_volatility
from src.features.technical import (
    compute_bollinger_bands,
    compute_macd,
    compute_moving_averages,
    compute_rsi,
)

logger = logging.getLogger(__name__)


def load_prices_for_ticker(engine: Engine, ticker: str) -> pd.DataFrame:
    """Load raw prices for a single ticker, ordered by timestamp.

    Args:
        engine: SQLAlchemy sync engine.
        ticker: Stock ticker symbol.

    Returns:
        DataFrame with timestamp index and OHLCV columns.
    """
    query = text("""
        SELECT timestamp, open, high, low, close, volume
        FROM raw_prices
        WHERE ticker = :ticker
        ORDER BY timestamp ASC
    """)

    with engine.connect() as conn:
        result = conn.execute(query, {"ticker": ticker})
        rows = result.fetchall()

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    df = df.set_index("timestamp")

    # Convert Decimal to float for computation
    for col in ["open", "high", "low", "close"]:
        df[col] = df[col].astype(float)
    df["volume"] = df["volume"].astype(int)

    return df


def compute_features_for_ticker(prices_df: pd.DataFrame) -> pd.DataFrame:
    """Compute all technical indicators and lag features for one ticker.

    Args:
        prices_df: DataFrame with timestamp index, must have 'close' column.

    Returns:
        DataFrame with all computed features, NaN warmup rows dropped.
    """
    if prices_df.empty:
        return pd.DataFrame()

    close = prices_df["close"]

    # Technical indicators
    rsi_14 = compute_rsi(close, period=14)
    macd_line, macd_signal = compute_macd(close)
    bb_upper, bb_lower = compute_bollinger_bands(close, period=20)
    sma_50, sma_200 = compute_moving_averages(close)

    # Lag features (for reference, not stored in technical_indicators table)
    lag_returns = compute_lag_returns(close)
    volatility = compute_volatility(close)

    # Assemble into a single DataFrame
    features = pd.DataFrame(
        {
            "rsi_14": rsi_14,
            "macd": macd_line,
            "macd_signal": macd_signal,
            "bollinger_upper": bb_upper,
            "bollinger_lower": bb_lower,
            "sma_50": sma_50,
            "sma_200": sma_200,
        },
        index=prices_df.index,
    )

    # Join lag features for logging/validation (not stored in DB)
    all_features = features.join(lag_returns).join(volatility.rename("volatility_20d"))

    # Drop rows where the core indicators are still in warmup (NaN)
    # SMA-200 requires the most warmup, so we use it as the cutoff
    features_clean = features.dropna(subset=["sma_200"])

    logger.debug(
        "Computed features: %d total rows, %d after dropping warmup (%d dropped)",
        len(features),
        len(features_clean),
        len(features) - len(features_clean),
    )

    return features_clean


def insert_features_to_db(
    engine: Engine,
    ticker: str,
    features_df: pd.DataFrame,
) -> int:
    """Insert computed features into technical_indicators table.

    Args:
        engine: SQLAlchemy sync engine.
        ticker: Stock ticker symbol.
        features_df: DataFrame with feature columns and timestamp index.

    Returns:
        Number of rows inserted.
    """
    if features_df.empty:
        return 0

    insert_sql = text("""
        INSERT INTO technical_indicators
            (ticker, timestamp, rsi_14, macd, macd_signal,
             bollinger_upper, bollinger_lower, sma_50, sma_200)
        VALUES
            (:ticker, :timestamp, :rsi_14, :macd, :macd_signal,
             :bollinger_upper, :bollinger_lower, :sma_50, :sma_200)
        ON CONFLICT (ticker, timestamp) DO NOTHING
    """)

    records = []
    for timestamp, row in features_df.iterrows():
        records.append({
            "ticker": ticker,
            "timestamp": timestamp,
            "rsi_14": round(float(row["rsi_14"]), 4),
            "macd": round(float(row["macd"]), 6),
            "macd_signal": round(float(row["macd_signal"]), 6),
            "bollinger_upper": round(float(row["bollinger_upper"]), 4),
            "bollinger_lower": round(float(row["bollinger_lower"]), 4),
            "sma_50": round(float(row["sma_50"]), 4),
            "sma_200": round(float(row["sma_200"]), 4),
        })

    inserted = 0
    batch_size = 1000
    with engine.begin() as conn:
        for i in range(0, len(records), batch_size):
            batch = records[i : i + batch_size]
            result = conn.execute(insert_sql, batch)
            inserted += result.rowcount

    return inserted


def get_all_tickers(engine: Engine) -> list[str]:
    """Get all distinct tickers from the raw_prices table."""
    query = text("SELECT DISTINCT ticker FROM raw_prices ORDER BY ticker")
    with engine.connect() as conn:
        result = conn.execute(query)
        return [row[0] for row in result]


def run_feature_pipeline(engine: Engine) -> dict[str, int]:
    """Run the full feature engineering pipeline for all tickers.

    Args:
        engine: SQLAlchemy sync engine.

    Returns:
        Dict mapping ticker -> number of feature rows inserted.
    """
    tickers = get_all_tickers(engine)
    logger.info("Running feature pipeline for %d tickers", len(tickers))

    results: dict[str, int] = {}
    total_inserted = 0

    for ticker in tickers:
        logger.info("Processing %s...", ticker)

        prices_df = load_prices_for_ticker(engine, ticker)
        if prices_df.empty:
            logger.warning("No price data for %s, skipping", ticker)
            results[ticker] = 0
            continue

        features_df = compute_features_for_ticker(prices_df)
        if features_df.empty:
            logger.warning("No features computed for %s (insufficient data)", ticker)
            results[ticker] = 0
            continue

        inserted = insert_features_to_db(engine, ticker, features_df)
        results[ticker] = inserted
        total_inserted += inserted

        logger.info(
            "%s: %d feature rows inserted (from %d price rows)",
            ticker, inserted, len(prices_df),
        )

    logger.info(
        "Feature pipeline complete: %d total rows inserted for %d tickers",
        total_inserted, len(tickers),
    )
    return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    from sqlalchemy import create_engine

    from src.config import settings

    sync_engine = create_engine(settings.database_url_sync)
    results = run_feature_pipeline(sync_engine)

    print("\nFeature Pipeline Results:")
    print("-" * 40)
    for ticker, count in sorted(results.items()):
        print(f"  {ticker}: {count} rows")
    print(f"\n  Total: {sum(results.values())} rows")