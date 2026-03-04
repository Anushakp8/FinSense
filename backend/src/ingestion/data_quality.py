"""Data quality validation checks for the FinSense pipeline.

Provides validation functions that run between pipeline steps to ensure
data integrity: null detection, outlier flagging, row count validation,
and data freshness checks.
"""

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import text
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)

# Maximum acceptable null percentage for critical columns
MAX_NULL_PERCENT = 5.0

# Maximum acceptable staleness (hours since last data point)
MAX_STALENESS_HOURS = 48  # Allow weekends (market closed Sat/Sun)

# Standard deviation threshold for outlier flagging
OUTLIER_STD_THRESHOLD = 3.0


class DataQualityError(Exception):
    """Raised when a data quality check fails."""


def check_null_rates(engine: Engine, table: str, columns: list[str]) -> dict[str, float]:
    """Check null rates for specified columns in a table.

    Args:
        engine: SQLAlchemy sync engine.
        table: Table name to check.
        columns: List of column names to check for nulls.

    Returns:
        Dict mapping column name to null percentage.

    Raises:
        DataQualityError: If any column exceeds MAX_NULL_PERCENT nulls.
    """
    results: dict[str, float] = {}

    with engine.connect() as conn:
        total_query = text(f"SELECT COUNT(*) FROM {table}")  # noqa: S608
        total_rows = conn.execute(total_query).scalar() or 0

        if total_rows == 0:
            logger.warning("Table %s is empty, skipping null check", table)
            return results

        for col in columns:
            null_query = text(
                f"SELECT COUNT(*) FROM {table} WHERE {col} IS NULL"  # noqa: S608
            )
            null_count = conn.execute(null_query).scalar() or 0
            null_pct = (null_count / total_rows) * 100.0
            results[col] = null_pct

            if null_pct > MAX_NULL_PERCENT:
                msg = (
                    f"Column {table}.{col} has {null_pct:.1f}% nulls "
                    f"(threshold: {MAX_NULL_PERCENT}%)"
                )
                logger.error(msg)
                raise DataQualityError(msg)

            logger.info(
                "Null check: %s.%s = %.2f%% nulls (OK)",
                table, col, null_pct,
            )

    return results


def check_data_freshness(engine: Engine, table: str = "raw_prices") -> float:
    """Check how fresh the latest data is.

    Args:
        engine: SQLAlchemy sync engine.
        table: Table to check freshness on.

    Returns:
        Hours since the most recent data point.

    Raises:
        DataQualityError: If data is staler than MAX_STALENESS_HOURS.
    """
    with engine.connect() as conn:
        query = text(f"SELECT MAX(timestamp) FROM {table}")  # noqa: S608
        latest = conn.execute(query).scalar()

    if latest is None:
        msg = f"No data found in {table}"
        raise DataQualityError(msg)

    if latest.tzinfo is None:
        latest = latest.replace(tzinfo=timezone.utc)

    now = datetime.now(timezone.utc)
    staleness_hours = (now - latest).total_seconds() / 3600.0

    logger.info(
        "Data freshness: latest record is %.1f hours old (threshold: %d hours)",
        staleness_hours,
        MAX_STALENESS_HOURS,
    )

    if staleness_hours > MAX_STALENESS_HOURS:
        msg = (
            f"Data in {table} is {staleness_hours:.1f} hours stale "
            f"(threshold: {MAX_STALENESS_HOURS} hours)"
        )
        logger.error(msg)
        raise DataQualityError(msg)

    return staleness_hours


def check_row_counts(
    engine: Engine,
    table: str,
    min_expected: int,
) -> int:
    """Validate that a table has at least the expected number of rows.

    Args:
        engine: SQLAlchemy sync engine.
        table: Table name to check.
        min_expected: Minimum expected row count.

    Returns:
        Actual row count.

    Raises:
        DataQualityError: If row count is below minimum.
    """
    with engine.connect() as conn:
        query = text(f"SELECT COUNT(*) FROM {table}")  # noqa: S608
        actual = conn.execute(query).scalar() or 0

    logger.info(
        "Row count: %s has %d rows (minimum expected: %d)",
        table, actual, min_expected,
    )

    if actual < min_expected:
        msg = (
            f"Table {table} has only {actual} rows "
            f"(expected at least {min_expected})"
        )
        logger.error(msg)
        raise DataQualityError(msg)

    return actual


def flag_outliers(engine: Engine, table: str = "raw_prices") -> dict[str, int]:
    """Flag price outliers per ticker (> 3 std devs from mean).

    This is a warning-only check â€” it does not raise errors.

    Args:
        engine: SQLAlchemy sync engine.
        table: Table to check.

    Returns:
        Dict mapping ticker to number of outlier rows flagged.
    """
    query = text("""
        WITH stats AS (
            SELECT
                ticker,
                AVG(close) as mean_close,
                STDDEV(close) as std_close
            FROM raw_prices
            GROUP BY ticker
        )
        SELECT
            rp.ticker,
            COUNT(*) as outlier_count
        FROM raw_prices rp
        JOIN stats s ON rp.ticker = s.ticker
        WHERE ABS(rp.close - s.mean_close) > :threshold * s.std_close
        GROUP BY rp.ticker
        ORDER BY rp.ticker
    """)

    outliers: dict[str, int] = {}
    with engine.connect() as conn:
        result = conn.execute(query, {"threshold": OUTLIER_STD_THRESHOLD})
        for row in result:
            outliers[row[0]] = row[1]
            logger.warning(
                "Outlier flag: %s has %d rows with close price > %.0f std devs from mean",
                row[0], row[1], OUTLIER_STD_THRESHOLD,
            )

    if not outliers:
        logger.info("No outliers detected across all tickers")

    return outliers


def run_all_quality_checks(engine: Engine) -> dict[str, object]:
    """Run all data quality checks and return a summary.

    Args:
        engine: SQLAlchemy sync engine.

    Returns:
        Dict with check results. Raises DataQualityError on critical failures.
    """
    logger.info("Running data quality checks...")

    results: dict[str, object] = {}

    # 1. Null rates on raw_prices
    results["null_rates"] = check_null_rates(
        engine, "raw_prices",
        ["ticker", "timestamp", "open", "high", "low", "close", "volume"],
    )

    # 2. Data freshness
    results["staleness_hours"] = check_data_freshness(engine)

    # 3. Row counts
    results["raw_prices_count"] = check_row_counts(engine, "raw_prices", min_expected=1000)

    # 4. Outlier flags (warning only)
    results["outliers"] = flag_outliers(engine)

    logger.info("All data quality checks passed")
    return results
