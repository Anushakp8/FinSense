"""Tests for lag features and volatility computations."""

import numpy as np
import pandas as pd

from src.features.lag_features import compute_lag_returns, compute_volatility


class TestComputeLagReturns:

    def test_empty_series(self) -> None:
        result = compute_lag_returns(pd.Series(dtype=float))
        assert result.empty

    def test_default_lags(self) -> None:
        """Should create columns for 1, 3, 5, 10 day lags."""
        prices = pd.Series(range(100, 120), dtype=float)
        result = compute_lag_returns(prices)
        assert list(result.columns) == ["return_1d", "return_3d", "return_5d", "return_10d"]

    def test_custom_lags(self) -> None:
        prices = pd.Series(range(100, 120), dtype=float)
        result = compute_lag_returns(prices, lags=[1, 2])
        assert list(result.columns) == ["return_1d", "return_2d"]

    def test_1day_return_correct(self) -> None:
        """1-day return from 100 to 110 should be 0.10."""
        prices = pd.Series([100.0, 110.0, 121.0])
        result = compute_lag_returns(prices, lags=[1])
        assert abs(result["return_1d"].iloc[1] - 0.10) < 0.001
        assert abs(result["return_1d"].iloc[2] - 0.10) < 0.001

    def test_first_values_are_nan(self) -> None:
        """First N values should be NaN for N-day lag."""
        prices = pd.Series(range(100, 120), dtype=float)
        result = compute_lag_returns(prices, lags=[5])
        assert result["return_5d"].iloc[:5].isna().all()
        assert result["return_5d"].iloc[5:].notna().all()

    def test_insufficient_data_for_lag(self) -> None:
        """If data length <= lag, column should be all NaN."""
        prices = pd.Series([100.0, 110.0])
        result = compute_lag_returns(prices, lags=[5])
        assert result["return_5d"].isna().all()


class TestComputeVolatility:

    def test_empty_series(self) -> None:
        result = compute_volatility(pd.Series(dtype=float))
        assert result.empty

    def test_insufficient_data(self) -> None:
        prices = pd.Series([100.0] * 10)
        result = compute_volatility(prices, window=20)
        assert result.isna().all() or result.empty

    def test_flat_prices_zero_vol(self) -> None:
        """Constant prices should produce zero volatility."""
        prices = pd.Series([100.0] * 50)
        result = compute_volatility(prices, window=20)
        valid = result.dropna()
        assert (valid == 0.0).all()

    def test_volatile_prices_positive_vol(self) -> None:
        """Volatile prices should produce positive volatility."""
        np.random.seed(42)
        prices = pd.Series(np.exp(np.cumsum(np.random.randn(100) * 0.02) + np.log(100)))
        result = compute_volatility(prices, window=20)
        valid = result.dropna()
        assert (valid > 0).all()

    def test_annualization(self) -> None:
        """Volatility should be annualized (multiplied by sqrt(252))."""
        np.random.seed(42)
        prices = pd.Series(np.exp(np.cumsum(np.random.randn(100) * 0.01) + np.log(100)))
        result = compute_volatility(prices, window=20)
        valid = result.dropna()
        # Daily vol ~0.01, annualized should be ~0.01 * sqrt(252) ~ 0.159
        assert valid.mean() > 0.05  # Should be clearly annualized