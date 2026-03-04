"""Lag features and volatility computations.

Computes lagged percentage returns and rolling volatility from
closing price series for use as ML model features.
"""

import pandas as pd


def compute_lag_returns(
    prices: pd.Series,
    lags: list[int] | None = None,
) -> pd.DataFrame:
    """Compute lagged percentage returns.

    Args:
        prices: Series of closing prices.
        lags: List of lag periods in trading days. Defaults to [1, 3, 5, 10].

    Returns:
        DataFrame with one column per lag, named 'return_Nd' (e.g. 'return_1d').
        Early values are NaN during warmup.
    """
    if lags is None:
        lags = [1, 3, 5, 10]

    if prices.empty:
        return pd.DataFrame(index=prices.index)

    result = pd.DataFrame(index=prices.index)

    for lag in lags:
        if len(prices) <= lag:
            result[f"return_{lag}d"] = pd.Series(dtype=float, index=prices.index)
        else:
            result[f"return_{lag}d"] = prices.pct_change(periods=lag)

    return result


def compute_volatility(
    prices: pd.Series,
    window: int = 20,
) -> pd.Series:
    """Compute rolling annualized volatility.

    Calculates the standard deviation of daily log returns over a rolling
    window, then annualizes by multiplying by sqrt(252).

    Args:
        prices: Series of closing prices.
        window: Rolling window size in trading days (default 20).

    Returns:
        Series of annualized volatility values. Early values are NaN.
    """
    if prices.empty or len(prices) < window + 1:
        return pd.Series(dtype=float, index=prices.index)

    import numpy as np

    log_returns = np.log(prices / prices.shift(1))
    rolling_vol = log_returns.rolling(window=window).std() * np.sqrt(252)

    return rolling_vol