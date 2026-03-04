"""Tests for the economic data fetcher."""

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from src.ingestion.economic_fetcher import (
    FRED_SERIES,
    fetch_economic_data,
    insert_economic_data_to_db,
)


class TestFetchEconomicData:

    def test_missing_api_key_raises_error(self) -> None:
        with patch("src.ingestion.economic_fetcher.settings") as mock_settings:
            mock_settings.fred_api_key = ""
            with pytest.raises(ValueError, match="FRED API key not configured"):
                fetch_economic_data()

    def test_placeholder_api_key_raises_error(self) -> None:
        with patch("src.ingestion.economic_fetcher.settings") as mock_settings:
            mock_settings.fred_api_key = "your_fred_api_key_here"
            with pytest.raises(ValueError, match="FRED API key not configured"):
                fetch_economic_data()

    def test_fred_series_has_expected_indicators(self) -> None:
        assert "GDP" in FRED_SERIES
        assert "CPIAUCSL" in FRED_SERIES
        assert "UNRATE" in FRED_SERIES
        assert "FEDFUNDS" in FRED_SERIES
        assert "DGS10" in FRED_SERIES

    @patch("src.ingestion.economic_fetcher.Fred")
    @patch("src.ingestion.economic_fetcher.settings")
    def test_successful_fetch(self, mock_settings: MagicMock, mock_fred_class: MagicMock) -> None:
        mock_settings.fred_api_key = "test_key_123"
        mock_fred = MagicMock()
        mock_fred_class.return_value = mock_fred

        dates = pd.date_range("2024-01-01", periods=3, freq="MS")
        mock_fred.get_series.return_value = pd.Series([3.5, 3.6, 3.4], index=dates)

        result = fetch_economic_data(
            series_map={"UNRATE": "Unemployment Rate"},
            start_date="2024-01-01",
        )
        assert not result.empty
        assert len(result) == 3
        assert all(result["series_id"] == "UNRATE")


class TestInsertEconomicData:

    def test_empty_df_returns_zero(self) -> None:
        engine = MagicMock()
        result = insert_economic_data_to_db(pd.DataFrame(), engine)
        assert result == 0