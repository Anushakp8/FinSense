"""Tests for the stock data fetcher."""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from src.ingestion.stock_fetcher import (
    TRACKED_TICKERS,
    fetch_historical_data,
    insert_prices_to_db,
)


class TestFetchHistoricalData:

    def test_invalid_period_raises_error(self) -> None:
        with pytest.raises(ValueError, match="Invalid period"):
            fetch_historical_data(period="invalid")

    def test_tracked_tickers_has_15_entries(self) -> None:
        assert len(TRACKED_TICKERS) == 15

    @patch("src.ingestion.stock_fetcher.yf.download")
    def test_empty_download_returns_empty_df(self, mock_download: MagicMock) -> None:
        mock_download.return_value = pd.DataFrame()
        result = fetch_historical_data(tickers=["AAPL"], period="1mo")
        assert result.empty

    @patch("src.ingestion.stock_fetcher.yf.download")
    def test_single_ticker_fetch(self, mock_download: MagicMock) -> None:
        dates = pd.date_range("2024-01-01", periods=5, freq="B")
        mock_df = pd.DataFrame(
            {
                "Open": [150.0, 151.0, 152.0, 153.0, 154.0],
                "High": [155.0, 156.0, 157.0, 158.0, 159.0],
                "Low": [149.0, 150.0, 151.0, 152.0, 153.0],
                "Close": [154.0, 155.0, 156.0, 157.0, 158.0],
                "Volume": [1000000, 1100000, 1200000, 1300000, 1400000],
            },
            index=dates,
        )
        mock_download.return_value = mock_df

        result = fetch_historical_data(tickers=["AAPL"], period="1mo")
        assert not result.empty
        assert len(result) == 5
        assert all(result["ticker"] == "AAPL")

    @patch("src.ingestion.stock_fetcher.yf.download")
    def test_drops_rows_with_nan_prices(self, mock_download: MagicMock) -> None:
        dates = pd.date_range("2024-01-01", periods=3, freq="B")
        mock_df = pd.DataFrame(
            {
                "Open": [150.0, float("nan"), 152.0],
                "High": [155.0, 156.0, 157.0],
                "Low": [149.0, 150.0, 151.0],
                "Close": [154.0, 155.0, 156.0],
                "Volume": [1000000, 1100000, 1200000],
            },
            index=dates,
        )
        mock_download.return_value = mock_df
        result = fetch_historical_data(tickers=["AAPL"], period="1mo")
        assert len(result) == 2

    @patch("src.ingestion.stock_fetcher.yf.download")
    def test_drops_rows_with_zero_volume(self, mock_download: MagicMock) -> None:
        dates = pd.date_range("2024-01-01", periods=3, freq="B")
        mock_df = pd.DataFrame(
            {
                "Open": [150.0, 151.0, 152.0],
                "High": [155.0, 156.0, 157.0],
                "Low": [149.0, 150.0, 151.0],
                "Close": [154.0, 155.0, 156.0],
                "Volume": [1000000, 0, 1200000],
            },
            index=dates,
        )
        mock_download.return_value = mock_df
        result = fetch_historical_data(tickers=["AAPL"], period="1mo")
        assert len(result) == 2

    @patch("src.ingestion.stock_fetcher.yf.download")
    def test_timestamps_have_utc_timezone(self, mock_download: MagicMock) -> None:
        dates = pd.date_range("2024-01-01", periods=2, freq="B")
        mock_df = pd.DataFrame(
            {
                "Open": [150.0, 151.0],
                "High": [155.0, 156.0],
                "Low": [149.0, 150.0],
                "Close": [154.0, 155.0],
                "Volume": [1000000, 1100000],
            },
            index=dates,
        )
        mock_download.return_value = mock_df
        result = fetch_historical_data(tickers=["AAPL"], period="1mo")
        for ts in result["timestamp"]:
            assert ts.tzinfo is not None


class TestInsertPricesToDb:

    def test_empty_df_returns_zero(self) -> None:
        engine = MagicMock()
        result = insert_prices_to_db(pd.DataFrame(), engine)
        assert result == 0

    def test_batch_insert_calls_engine(self) -> None:
        df = pd.DataFrame([{
            "ticker": "AAPL",
            "timestamp": datetime(2024, 1, 2, tzinfo=timezone.utc),
            "open": 150.0, "high": 155.0, "low": 149.0, "close": 154.0, "volume": 1000000,
        }])

        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_conn.execute.return_value = mock_result
        mock_engine.begin.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_engine.begin.return_value.__exit__ = MagicMock(return_value=False)

        result = insert_prices_to_db(df, mock_engine)
        assert result == 1
        mock_conn.execute.assert_called_once()