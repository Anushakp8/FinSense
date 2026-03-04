"""Economic data fetcher using the FRED API."""

import logging
from datetime import timezone

import pandas as pd
from fredapi import Fred
from sqlalchemy import text
from sqlalchemy.engine import Engine

from src.config import settings

logger = logging.getLogger(__name__)

FRED_SERIES: dict[str, str] = {
    "GDP": "Gross Domestic Product",
    "CPIAUCSL": "Consumer Price Index (All Urban)",
    "UNRATE": "Unemployment Rate",
    "FEDFUNDS": "Federal Funds Effective Rate",
    "DGS10": "10-Year Treasury Constant Maturity Rate",
}


def fetch_economic_data(
    series_map: dict[str, str] | None = None,
    start_date: str = "2020-01-01",
) -> pd.DataFrame:
    """Fetch economic indicator data from the FRED API."""
    if not settings.fred_api_key or settings.fred_api_key == "your_fred_api_key_here":
        msg = (
            "FRED API key not configured. "
            "Set FRED_API_KEY in your .env file. "
            "Get a free key at https://fred.stlouisfed.org/docs/api/api_key.html"
        )
        raise ValueError(msg)

    series_map = series_map or FRED_SERIES
    fred = Fred(api_key=settings.fred_api_key)
    records: list[dict[str, object]] = []

    for series_id, name in series_map.items():
        try:
            logger.info("Fetching FRED series: %s (%s)", series_id, name)
            series_data = fred.get_series(series_id, observation_start=start_date)

            if series_data is None or series_data.empty:
                logger.warning("No data returned for series %s", series_id)
                continue

            series_data = series_data.dropna()

            for timestamp, value in series_data.items():
                ts = pd.Timestamp(timestamp)
                records.append({
                    "series_id": series_id,
                    "name": name,
                    "timestamp": ts.to_pydatetime().replace(tzinfo=timezone.utc),
                    "value": round(float(value), 6),
                })

            logger.info("Fetched %d data points for %s", len(series_data), series_id)

        except Exception:
            logger.exception("Failed to fetch series %s", series_id)
            continue

    if not records:
        logger.warning("No economic data fetched")
        return pd.DataFrame()

    result_df = pd.DataFrame(records)
    logger.info(
        "Fetched %d total economic data points across %d series",
        len(result_df), result_df["series_id"].nunique(),
    )
    return result_df


def insert_economic_data_to_db(df: pd.DataFrame, engine: Engine) -> int:
    """Insert economic indicator data with deduplication."""
    if df.empty:
        logger.warning("Empty DataFrame, nothing to insert")
        return 0

    insert_sql = text("""
        INSERT INTO economic_indicators (series_id, name, timestamp, value)
        VALUES (:series_id, :name, :timestamp, :value)
        ON CONFLICT (series_id, timestamp) DO NOTHING
    """)

    records = df.to_dict(orient="records")
    inserted = 0

    batch_size = 500
    with engine.begin() as conn:
        for i in range(0, len(records), batch_size):
            batch = records[i : i + batch_size]
            result = conn.execute(insert_sql, batch)
            inserted += result.rowcount

    logger.info("Inserted %d new rows out of %d total", inserted, len(records))
    return inserted


def run_economic_ingestion(engine: Engine) -> int:
    """Run the full economic data ingestion pipeline."""
    df = fetch_economic_data()
    if df.empty:
        return 0
    return insert_economic_data_to_db(df, engine)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    from sqlalchemy import create_engine

    sync_engine = create_engine(settings.database_url_sync)
    count = run_economic_ingestion(sync_engine)
    print(f"\nDone! Inserted {count} rows into economic_indicators.")