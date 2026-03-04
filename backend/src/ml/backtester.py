"""Historical backtesting engine.

Evaluates model predictions against held-out historical data,
computing accuracy, Sharpe ratio, max drawdown, and win rate.
Compares against a buy-and-hold baseline.
"""

import logging

import numpy as np
import pandas as pd
from sqlalchemy.engine import Engine

from src.ml.trainer import TRAIN_WINDOW, get_feature_columns, load_training_data

logger = logging.getLogger(__name__)

# Backtest on the most recent 6 months (~126 trading days)
BACKTEST_DAYS = 126


def run_backtest(
    engine: Engine,
    model: object,
    ticker: str,
    backtest_days: int = BACKTEST_DAYS,
) -> dict[str, object]:
    """Run a backtest on held-out historical data.

    Uses the last `backtest_days` of data as the test set,
    generates predictions, and computes performance metrics.

    Args:
        engine: SQLAlchemy sync engine.
        model: Trained sklearn-compatible model with predict/predict_proba.
        ticker: Stock ticker symbol.
        backtest_days: Number of days to backtest on.

    Returns:
        Dict with backtest metrics and per-day results.
    """
    logger.info("Running backtest for %s (%d days)", ticker, backtest_days)

    df = load_training_data(engine, ticker)
    if df.empty or len(df) < TRAIN_WINDOW + backtest_days:
        logger.warning("Insufficient data for backtest (%d rows)", len(df))
        return {"status": "insufficient_data", "rows": len(df)}

    # Use the last N days as backtest period
    backtest_df = df.iloc[-backtest_days:].copy()
    feature_cols = get_feature_columns()

    X_test = backtest_df[feature_cols].values
    y_true = backtest_df["target"].values
    closes = backtest_df["close"].values
    timestamps = backtest_df["timestamp"].values

    # Generate predictions
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    # â”€â”€ Core metrics â”€â”€
    accuracy = float(np.mean(y_pred == y_true))
    win_rate = float(np.mean(y_pred == y_true))

    # Precision/Recall/F1 for the "UP" class
    true_pos = np.sum((y_pred == 1) & (y_true == 1))
    false_pos = np.sum((y_pred == 1) & (y_true == 0))
    false_neg = np.sum((y_pred == 0) & (y_true == 1))

    precision = true_pos / (true_pos + false_pos) if (true_pos + false_pos) > 0 else 0.0
    recall = true_pos / (true_pos + false_neg) if (true_pos + false_neg) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    # â”€â”€ Strategy returns â”€â”€
    # Simple strategy: go long when model predicts UP, flat when DOWN
    daily_returns = np.diff(closes) / closes[:-1]

    # Strategy: multiply return by prediction (1 if UP, 0 if DOWN)
    strategy_returns = daily_returns * y_pred[:-1]

    # Buy and hold: just use raw daily returns
    buyhold_returns = daily_returns

    # â”€â”€ Sharpe Ratio (annualized) â”€â”€
    if len(strategy_returns) > 0 and np.std(strategy_returns) > 0:
        sharpe_ratio = float(
            np.mean(strategy_returns) / np.std(strategy_returns) * np.sqrt(252)
        )
    else:
        sharpe_ratio = 0.0

    # â”€â”€ Max Drawdown â”€â”€
    cumulative = np.cumprod(1 + strategy_returns)
    running_max = np.maximum.accumulate(cumulative)
    drawdowns = (cumulative - running_max) / running_max
    max_drawdown = float(np.min(drawdowns)) if len(drawdowns) > 0 else 0.0

    # â”€â”€ Buy & Hold metrics â”€â”€
    if len(buyhold_returns) > 0 and np.std(buyhold_returns) > 0:
        buyhold_sharpe = float(
            np.mean(buyhold_returns) / np.std(buyhold_returns) * np.sqrt(252)
        )
    else:
        buyhold_sharpe = 0.0

    buyhold_cumulative = np.cumprod(1 + buyhold_returns)
    buyhold_total_return = float(buyhold_cumulative[-1] - 1) if len(buyhold_cumulative) > 0 else 0.0
    strategy_total_return = float(cumulative[-1] - 1) if len(cumulative) > 0 else 0.0

    report = {
        "status": "success",
        "ticker": ticker,
        "backtest_days": backtest_days,
        "accuracy": round(accuracy, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "win_rate": round(win_rate, 4),
        "sharpe_ratio": round(sharpe_ratio, 4),
        "max_drawdown": round(max_drawdown, 4),
        "strategy_total_return": round(strategy_total_return, 4),
        "buyhold_total_return": round(buyhold_total_return, 4),
        "buyhold_sharpe": round(buyhold_sharpe, 4),
        "outperformance": round(strategy_total_return - buyhold_total_return, 4),
    }

    logger.info(
        "Backtest results for %s: Acc=%.4f F1=%.4f Sharpe=%.4f MaxDD=%.4f",
        ticker, accuracy, f1, sharpe_ratio, max_drawdown,
    )

    return report


def run_multi_ticker_backtest(
    engine: Engine,
    model: object,
    tickers: list[str] | None = None,
) -> dict[str, object]:
    """Run backtests across multiple tickers.

    Args:
        engine: SQLAlchemy sync engine.
        model: Trained model.
        tickers: List of tickers. Defaults to all tickers in DB.

    Returns:
        Dict with per-ticker and aggregate results.
    """
    if tickers is None:
        from src.features.pipeline import get_all_tickers
        tickers = get_all_tickers(engine)

    all_results: dict[str, dict[str, object]] = {}
    for ticker in tickers:
        all_results[ticker] = run_backtest(engine, model, ticker)

    # Compute aggregate metrics
    successful = {k: v for k, v in all_results.items() if v.get("status") == "success"}

    if successful:
        avg_accuracy = np.mean([v["accuracy"] for v in successful.values()])
        avg_f1 = np.mean([v["f1"] for v in successful.values()])
        avg_sharpe = np.mean([v["sharpe_ratio"] for v in successful.values()])

        aggregate = {
            "tickers_tested": len(successful),
            "avg_accuracy": round(float(avg_accuracy), 4),
            "avg_f1": round(float(avg_f1), 4),
            "avg_sharpe": round(float(avg_sharpe), 4),
        }
    else:
        aggregate = {"tickers_tested": 0}

    return {
        "per_ticker": all_results,
        "aggregate": aggregate,
    }
