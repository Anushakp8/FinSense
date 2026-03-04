"""Stock data fetcher using yfinance.

Fetches historical OHLCV data for tracked tickers and inserts into the
raw_prices table with deduplication via ON CONFLICT DO NOTHING.
"""

import logging
from datetime import datetime, timezone

import pandas as pd
import yfinance as yf
from sqlalchemy import text
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)

TRACKED_TICKERS: list[str] = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA",
    "META", "TSLA", "JPM", "V", "JNJ",
    "WMT", "PG", "DIS", "NFLX", "AMD",
]

VALID_PERIODS: list[str] = [
    "1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max",
]


def fetch_historical_data(
    tickers: list[str] | None = None,
    period: str = "2y",
) -> pd.DataFrame:
    """Fetch historical OHLCV data from Yahoo Finance."""
    if period not in VALID_PERIODS:
        msg = f"Invalid period '{period}'. Must be one of: {VALID_PERIODS}"
        raise ValueError(msg)

    tickers = tickers or TRACKED_TICKERS
    logger.info("Fetching %s of historical data for %d tickers", period, len(tickers))

    raw_df = yf.download(
        tickers=tickers,
        period=period,
        interval="1d",
        group_by="ticker",
        auto_adjust=True,
        threads=True,
    )

    if raw_df.empty:
        logger.warning("No data returned from yfinance")
        return pd.DataFrame()

    records: list[dict[str, object]] = []

    for ticker in tickers:
        try:
            if len(tickers) == 1:
                ticker_df = raw_df.copy()
            else:
                ticker_df = raw_df[ticker].copy()

            ticker_df = ticker_df.dropna(how="all")

            if ticker_df.empty:
                logger.warning("No data for ticker %s, skipping", ticker)
                continue

            for idx, row in ticker_df.iterrows():
                if pd.isna(row.get("Open")) or pd.isna(row.get("Close")):
                    continue

                timestamp = idx if isinstance(idx, datetime) else pd.Timestamp(idx)

                records.append({
                    "ticker": ticker,
                    "timestamp": timestamp.to_pydatetime().replace(tzinfo=timezone.utc),
                    "open": round(float(row["Open"]), 4),
                    "high": round(float(row["High"]), 4),
                    "low": round(float(row["Low"]), 4),
                    "close": round(float(row["Close"]), 4),
                    "volume": int(row["Volume"]),
                })
        except KeyError:
            logger.warning("Ticker %s not found in downloaded data, skipping", ticker)
            continue

    if not records:
        logger.warning("No valid records after cleaning")
        return pd.DataFrame()

    result_df = pd.DataFrame(records)

    before_count = len(result_df)
    result_df = result_df[
        (result_df["open"] > 0)
        & (result_df["high"] > 0)
        & (result_df["low"] > 0)
        & (result_df["close"] > 0)
        & (result_df["volume"] > 0)
    ]
    dropped = before_count - len(result_df)
    if dropped > 0:
        logger.info("Dropped %d rows with invalid prices or zero volume", dropped)

    for ticker in result_df["ticker"].unique():
        ticker_mask = result_df["ticker"] == ticker
        close_prices = result_df.loc[ticker_mask, "close"]
        mean_price = close_prices.mean()
        std_price = close_prices.std()
        if std_price > 0:
            outlier_mask = ticker_mask & (
                (result_df["close"] - mean_price).abs() > 3 * std_price
            )
            outlier_count = outlier_mask.sum()
            if outlier_count > 0:
                logger.warning(
                    "Ticker %s has %d potential outlier rows (>3 sigma from mean)",
                    ticker, outlier_count,
                )

    logger.info("Fetched %d records for %d tickers", len(result_df), result_df["ticker"].nunique())
    return result_df


def insert_prices_to_db(df: pd.DataFrame, engine: Engine) -> int:
    """Insert price data into raw_prices table with deduplication."""
    if df.empty:
        logger.warning("Empty DataFrame, nothing to insert")
        return 0

    insert_sql = text("""
        INSERT INTO raw_prices (ticker, timestamp, open, high, low, close, volume)
        VALUES (:ticker, :timestamp, :open, :high, :low, :close, :volume)
        ON CONFLICT (ticker, timestamp) DO NOTHING
    """)

    records = df.to_dict(orient="records")
    inserted = 0

    batch_size = 1000
    with engine.begin() as conn:
        for i in range(0, len(records), batch_size):
            batch = records[i : i + batch_size]
            result = conn.execute(insert_sql, batch)
            inserted += result.rowcount

    logger.info(
        "Inserted %d new rows out of %d total (skipped %d duplicates)",
        inserted, len(records), len(records) - inserted,
    )
    return inserted


def run_stock_ingestion(engine: Engine, period: str = "2y") -> int:
    """Run the full stock ingestion pipeline."""
    df = fetch_historical_data(period=period)
    if df.empty:
        return 0
    return insert_prices_to_db(df, engine)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    from sqlalchemy import create_engine
    from src.config import settings

    sync_engine = create_engine(settings.database_url_sync)
    count = run_stock_ingestion(sync_engine)
    print(f"\nDone! Inserted {count} rows into raw_prices.")