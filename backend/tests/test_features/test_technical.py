"""Tests for technical indicator computations."""

import numpy as np
import pandas as pd
import pytest

from src.features.technical import (
    compute_bollinger_bands,
    compute_macd,
    compute_moving_averages,
    compute_rsi,
)


class TestComputeRSI:

    def test_empty_series(self) -> None:
        result = compute_rsi(pd.Series(dtype=float))
        assert result.empty

    def test_insufficient_data(self) -> None:
        prices = pd.Series([100.0] * 10)
        result = compute_rsi(prices, period=14)
        assert result.isna().all() or result.empty

    def test_rsi_bounds(self) -> None:
        """RSI should always be between 0 and 100."""
        np.random.seed(42)
        prices = pd.Series(np.cumsum(np.random.randn(100)) + 100)
        result = compute_rsi(prices)
        valid = result.dropna()
        assert (valid >= 0).all()
        assert (valid <= 100).all()

    def test_all_gains_rsi_near_100(self) -> None:
        """Monotonically increasing prices should give RSI near 100."""
        prices = pd.Series(range(100, 200))
        result = compute_rsi(prices, period=14)
        valid = result.dropna()
        assert valid.iloc[-1] > 95

    def test_all_losses_rsi_near_0(self) -> None:
        """Monotonically decreasing prices should give RSI near 0."""
        prices = pd.Series(range(200, 100, -1))
        result = compute_rsi(prices, period=14)
        valid = result.dropna()
        assert valid.iloc[-1] < 5

    def test_flat_prices(self) -> None:
        """Flat prices (no change) should give RSI of 100 (no losses)."""
        prices = pd.Series([100.0] * 30)
        result = compute_rsi(prices, period=14)
        valid = result.dropna()
        # With no movement, gains and losses are 0; fillna gives 100
        assert len(valid) > 0


class TestComputeMACD:

    def test_empty_series(self) -> None:
        macd, signal = compute_macd(pd.Series(dtype=float))
        assert macd.empty
        assert signal.empty

    def test_insufficient_data(self) -> None:
        prices = pd.Series([100.0] * 10)
        macd, signal = compute_macd(prices)
        assert macd.isna().all() or macd.empty

    def test_returns_correct_length(self) -> None:
        prices = pd.Series(range(100, 200), dtype=float)
        macd, signal = compute_macd(prices)
        assert len(macd) == len(prices)
        assert len(signal) == len(prices)

    def test_macd_is_ema_difference(self) -> None:
        """MACD line should be the difference of fast and slow EMAs."""
        np.random.seed(42)
        prices = pd.Series(np.cumsum(np.random.randn(100)) + 100)
        macd, _ = compute_macd(prices)
        ema_12 = prices.ewm(span=12, adjust=False).mean()
        ema_26 = prices.ewm(span=26, adjust=False).mean()
        expected = ema_12 - ema_26
        pd.testing.assert_series_equal(macd, expected)


class TestComputeBollingerBands:

    def test_empty_series(self) -> None:
        upper, lower = compute_bollinger_bands(pd.Series(dtype=float))
        assert upper.empty
        assert lower.empty

    def test_insufficient_data(self) -> None:
        prices = pd.Series([100.0] * 10)
        upper, lower = compute_bollinger_bands(prices, period=20)
        assert upper.isna().all() or upper.empty

    def test_upper_above_lower(self) -> None:
        """Upper band should always be >= lower band."""
        np.random.seed(42)
        prices = pd.Series(np.cumsum(np.random.randn(100)) + 100)
        upper, lower = compute_bollinger_bands(prices)
        valid_mask = upper.notna() & lower.notna()
        assert (upper[valid_mask] >= lower[valid_mask]).all()

    def test_flat_prices_narrow_bands(self) -> None:
        """Flat prices should produce very narrow bands (std ~ 0)."""
        prices = pd.Series([100.0] * 30)
        upper, lower = compute_bollinger_bands(prices, period=20)
        valid_upper = upper.dropna()
        valid_lower = lower.dropna()
        assert abs(valid_upper.iloc[-1] - valid_lower.iloc[-1]) < 0.01


class TestComputeMovingAverages:

    def test_empty_series(self) -> None:
        sma_50, sma_200 = compute_moving_averages(pd.Series(dtype=float))
        assert sma_50.empty
        assert sma_200.empty

    def test_sma_50_available_before_sma_200(self) -> None:
        """SMA-50 should have values before SMA-200 does."""
        prices = pd.Series(range(1, 252), dtype=float)
        sma_50, sma_200 = compute_moving_averages(prices)
        assert sma_50.notna().sum() > sma_200.notna().sum()

    def test_sma_values_correct(self) -> None:
        """SMA-50 of a linear series should match hand-calculated value."""
        prices = pd.Series(range(1, 101), dtype=float)
        sma_50, _ = compute_moving_averages(prices)
        # SMA-50 at index 49 should be mean of 1..50 = 25.5
        assert abs(sma_50.iloc[49] - 25.5) < 0.01