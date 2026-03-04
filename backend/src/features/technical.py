"""Technical indicator computations.

All functions accept a pandas Series of closing prices and return
computed indicator values. They handle edge cases like insufficient
data and NaN values gracefully.
"""

import pandas as pd


def compute_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    """Compute Relative Strength Index (RSI).

    Args:
        prices: Series of closing prices.
        period: Lookback period (default 14).

    Returns:
        Series of RSI values (0-100). Early values are NaN during warmup.
    """
    if prices.empty or len(prices) < period + 1:
        return pd.Series(dtype=float, index=prices.index)

    delta = prices.diff()
    gains = delta.where(delta > 0, 0.0)
    losses = (-delta).where(delta < 0, 0.0)

    # Use exponential weighted mean (Wilder's smoothing)
    avg_gain = gains.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()
    avg_loss = losses.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()

    rs = avg_gain / avg_loss.replace(0, float("nan"))
    rsi = 100.0 - (100.0 / (1.0 + rs))

    # RSI is undefined when avg_loss is 0 (all gains) -> set to 100
    rsi = rsi.fillna(100.0)

    return rsi


def compute_macd(
    prices: pd.Series,
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9,
) -> tuple[pd.Series, pd.Series]:
    """Compute MACD line and signal line.

    Args:
        prices: Series of closing prices.
        fast_period: Fast EMA period (default 12).
        slow_period: Slow EMA period (default 26).
        signal_period: Signal line EMA period (default 9).

    Returns:
        Tuple of (macd_line, signal_line). Early values are NaN.
    """
    if prices.empty or len(prices) < slow_period:
        empty = pd.Series(dtype=float, index=prices.index)
        return empty, empty.copy()

    ema_fast = prices.ewm(span=fast_period, adjust=False).mean()
    ema_slow = prices.ewm(span=slow_period, adjust=False).mean()

    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()

    return macd_line, signal_line


def compute_bollinger_bands(
    prices: pd.Series,
    period: int = 20,
    num_std: float = 2.0,
) -> tuple[pd.Series, pd.Series]:
    """Compute Bollinger Bands (upper and lower).

    Args:
        prices: Series of closing prices.
        period: SMA lookback period (default 20).
        num_std: Number of standard deviations (default 2.0).

    Returns:
        Tuple of (upper_band, lower_band). Early values are NaN.
    """
    if prices.empty or len(prices) < period:
        empty = pd.Series(dtype=float, index=prices.index)
        return empty, empty.copy()

    sma = prices.rolling(window=period).mean()
    rolling_std = prices.rolling(window=period).std()

    upper_band = sma + (num_std * rolling_std)
    lower_band = sma - (num_std * rolling_std)

    return upper_band, lower_band


def compute_moving_averages(
    prices: pd.Series,
    short_period: int = 50,
    long_period: int = 200,
) -> tuple[pd.Series, pd.Series]:
    """Compute simple moving averages (SMA).

    Args:
        prices: Series of closing prices.
        short_period: Short SMA period (default 50).
        long_period: Long SMA period (default 200).

    Returns:
        Tuple of (sma_short, sma_long). Early values are NaN.
    """
    if prices.empty:
        empty = pd.Series(dtype=float, index=prices.index)
        return empty, empty.copy()

    sma_short = prices.rolling(window=short_period, min_periods=short_period).mean()
    sma_long = prices.rolling(window=long_period, min_periods=long_period).mean()

    return sma_short, sma_long