"""Run full backtest and generate report.

Executes the backtester across all 15 tickers using the active model
and prints a comprehensive performance report.
"""

import json
import logging
import sys

from sqlalchemy import create_engine

from src.config import settings
from src.ml.backtester import run_backtest, run_multi_ticker_backtest
from src.ml.registry import get_active_model

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    engine = create_engine(settings.database_url_sync)

    # Load active model
    model_result = get_active_model(engine)
    if model_result is None:
        print("ERROR: No active model found. Train and promote a model first.")
        sys.exit(1)

    model_data, metadata = model_result

    # Handle dict format (model + scaler saved together)
    if isinstance(model_data, dict):
        model = model_data["model"]
    else:
        model = model_data

    print("=" * 70)
    print("  FinSense Backtest Report")
    print("=" * 70)
    print(f"\n  Model: {metadata['model_name']} v{metadata['version']}")
    print(f"  Training F1: {metadata['f1']:.4f}")
    print(f"  Backtest period: Last 126 trading days (~6 months)\n")

    # Run multi-ticker backtest
    results = run_multi_ticker_backtest(engine, model)

    # Print per-ticker results
    print("-" * 70)
    print(f"  {'Ticker':<8} {'Accuracy':>10} {'F1':>8} {'Sharpe':>8} {'MaxDD':>8} {'Strategy':>10} {'BuyHold':>10}")
    print("-" * 70)

    for ticker, report in sorted(results["per_ticker"].items()):
        if report.get("status") != "success":
            print(f"  {ticker:<8} {'SKIPPED':>10} (insufficient data)")
            continue

        print(
            f"  {ticker:<8} "
            f"{report['accuracy']:>9.1%} "
            f"{report['f1']:>7.1%} "
            f"{report['sharpe_ratio']:>+7.2f} "
            f"{report['max_drawdown']:>7.1%} "
            f"{report['strategy_total_return']:>+9.1%} "
            f"{report['buyhold_total_return']:>+9.1%}"
        )

    # Print aggregate
    agg = results["aggregate"]
    print("-" * 70)
    print(f"\n  Aggregate Results ({agg.get('tickers_tested', 0)} tickers):")
    print(f"    Average Accuracy:  {agg.get('avg_accuracy', 0):.1%}")
    print(f"    Average F1 Score:  {agg.get('avg_f1', 0):.1%}")
    print(f"    Average Sharpe:    {agg.get('avg_sharpe', 0):+.4f}")

    print("\n" + "=" * 70)

    # Save report as JSON
    report_path = "./backtest_report.json"
    with open(report_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n  Full report saved to: {report_path}")


if __name__ == "__main__":
    main()
