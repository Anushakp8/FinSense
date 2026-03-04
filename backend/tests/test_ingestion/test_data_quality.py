"""Tests for data quality validation module."""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest

from src.ingestion.data_quality import (
    DataQualityError,
    check_data_freshness,
    check_null_rates,
    check_row_counts,
)


class TestCheckNullRates:

    def test_empty_table_skips(self) -> None:
        """Should skip check and return empty dict for empty table."""
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_conn.execute.return_value.scalar.return_value = 0
        mock_engine.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_engine.connect.return_value.__exit__ = MagicMock(return_value=False)

        result = check_null_rates(mock_engine, "raw_prices", ["close"])
        assert result == {}

    def test_high_null_rate_raises_error(self) -> None:
        """Should raise DataQualityError when nulls exceed threshold."""
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        # First call: total count = 100, Second call: null count = 10 (10%)
        mock_conn.execute.return_value.scalar.side_effect = [100, 10]
        mock_engine.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_engine.connect.return_value.__exit__ = MagicMock(return_value=False)

        with pytest.raises(DataQualityError, match="nulls"):
            check_null_rates(mock_engine, "raw_prices", ["close"])

    def test_low_null_rate_passes(self) -> None:
        """Should pass when null rate is below threshold."""
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        # Total: 1000, Nulls: 10 (1%)
        mock_conn.execute.return_value.scalar.side_effect = [1000, 10]
        mock_engine.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_engine.connect.return_value.__exit__ = MagicMock(return_value=False)

        result = check_null_rates(mock_engine, "raw_prices", ["close"])
        assert result["close"] == 1.0


class TestCheckDataFreshness:

    def test_no_data_raises_error(self) -> None:
        """Should raise when table is empty."""
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_conn.execute.return_value.scalar.return_value = None
        mock_engine.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_engine.connect.return_value.__exit__ = MagicMock(return_value=False)

        with pytest.raises(DataQualityError, match="No data found"):
            check_data_freshness(mock_engine)

    def test_fresh_data_passes(self) -> None:
        """Should pass when data is recent."""
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        recent = datetime.now(timezone.utc) - timedelta(hours=2)
        mock_conn.execute.return_value.scalar.return_value = recent
        mock_engine.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_engine.connect.return_value.__exit__ = MagicMock(return_value=False)

        hours = check_data_freshness(mock_engine)
        assert hours < 3

    def test_stale_data_raises_error(self) -> None:
        """Should raise when data is too old."""
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        old = datetime.now(timezone.utc) - timedelta(hours=100)
        mock_conn.execute.return_value.scalar.return_value = old
        mock_engine.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_engine.connect.return_value.__exit__ = MagicMock(return_value=False)

        with pytest.raises(DataQualityError, match="stale"):
            check_data_freshness(mock_engine)


class TestCheckRowCounts:

    def test_sufficient_rows_passes(self) -> None:
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_conn.execute.return_value.scalar.return_value = 5000
        mock_engine.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_engine.connect.return_value.__exit__ = MagicMock(return_value=False)

        count = check_row_counts(mock_engine, "raw_prices", min_expected=1000)
        assert count == 5000

    def test_insufficient_rows_raises_error(self) -> None:
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_conn.execute.return_value.scalar.return_value = 50
        mock_engine.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_engine.connect.return_value.__exit__ = MagicMock(return_value=False)

        with pytest.raises(DataQualityError, match="only 50 rows"):
            check_row_counts(mock_engine, "raw_prices", min_expected=1000)
