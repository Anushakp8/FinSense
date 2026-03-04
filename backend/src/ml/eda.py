"""Exploratory Data Analysis (EDA) for the FinSense training pipeline.

Generates a comprehensive data quality and distribution report before
model training. Covers: missing values, duplicates, class balance,
feature distributions, correlations, and outlier analysis.
"""

import logging

import numpy as np
import pandas as pd
from sqlalchemy.engine import Engine

from src.ml.trainer import get_feature_columns, load_training_data

logger = logging.getLogger(__name__)


def analyze_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """Analyze missing values per column.

    Returns:
        DataFrame with columns: column, missing_count, missing_pct, dtype.
    """
    total = len(df)
    records = []
    for col in df.columns:
        missing = int(df[col].isna().sum())
        records.append({
            "column": col,
            "missing_count": missing,
            "missing_pct": round(missing / total * 100, 2) if total > 0 else 0.0,
            "dtype": str(df[col].dtype),
        })
    return pd.DataFrame(records).sort_values("missing_pct", ascending=False)


def analyze_duplicates(df: pd.DataFrame) -> dict[str, int]:
    """Check for duplicate rows in the dataset.

    Returns:
        Dict with total_rows, duplicate_rows, unique_rows.
    """
    total = len(df)
    dupes = int(df.duplicated().sum())
    return {
        "total_rows": total,
        "duplicate_rows": dupes,
        "unique_rows": total - dupes,
        "duplicate_pct": round(dupes / total * 100, 2) if total > 0 else 0.0,
    }


def analyze_class_balance(df: pd.DataFrame, target_col: str = "target") -> dict[str, object]:
    """Analyze target variable class distribution.

    Returns:
        Dict with class counts, percentages, and balance ratio.
    """
    if target_col not in df.columns:
        return {"error": f"Column '{target_col}' not found"}

    counts = df[target_col].value_counts()
    total = len(df)

    up_count = int(counts.get(1, 0))
    down_count = int(counts.get(0, 0))
    balance_ratio = min(up_count, down_count) / max(up_count, down_count) if max(up_count, down_count) > 0 else 0

    return {
        "up_days": up_count,
        "down_days": down_count,
        "up_pct": round(up_count / total * 100, 2) if total > 0 else 0.0,
        "down_pct": round(down_count / total * 100, 2) if total > 0 else 0.0,
        "balance_ratio": round(balance_ratio, 4),
        "is_balanced": balance_ratio > 0.7,  # >70% ratio is considered balanced
    }


def analyze_feature_distributions(df: pd.DataFrame, feature_cols: list[str]) -> pd.DataFrame:
    """Compute distribution statistics for all features.

    Returns:
        DataFrame with mean, std, min, max, skewness, kurtosis per feature.
    """
    records = []
    for col in feature_cols:
        if col not in df.columns:
            continue
        series = df[col].dropna()
        if series.empty:
            continue
        records.append({
            "feature": col,
            "mean": round(float(series.mean()), 6),
            "std": round(float(series.std()), 6),
            "min": round(float(series.min()), 6),
            "max": round(float(series.max()), 6),
            "median": round(float(series.median()), 6),
            "skewness": round(float(series.skew()), 4),
            "kurtosis": round(float(series.kurtosis()), 4),
            "range": round(float(series.max() - series.min()), 6),
        })
    return pd.DataFrame(records)


def analyze_correlations(df: pd.DataFrame, feature_cols: list[str]) -> dict[str, object]:
    """Analyze feature-to-feature and feature-to-target correlations.

    Returns:
        Dict with correlation matrix and highly correlated feature pairs.
    """
    available_cols = [c for c in feature_cols if c in df.columns]
    if "target" in df.columns:
        available_cols.append("target")

    corr_matrix = df[available_cols].corr()

    # Find highly correlated feature pairs (|r| > 0.8)
    high_corr_pairs = []
    for i, col1 in enumerate(available_cols):
        for j, col2 in enumerate(available_cols):
            if i >= j or col1 == "target" or col2 == "target":
                continue
            r = corr_matrix.loc[col1, col2]
            if abs(r) > 0.8:
                high_corr_pairs.append({
                    "feature_1": col1,
                    "feature_2": col2,
                    "correlation": round(float(r), 4),
                })

    # Feature-to-target correlations
    target_corrs = {}
    if "target" in corr_matrix.columns:
        for col in available_cols:
            if col != "target":
                target_corrs[col] = round(float(corr_matrix.loc[col, "target"]), 4)

    return {
        "high_correlation_pairs": high_corr_pairs,
        "target_correlations": target_corrs,
    }


def analyze_outliers(df: pd.DataFrame, feature_cols: list[str], threshold: float = 3.0) -> pd.DataFrame:
    """Detect outliers using z-score method.

    Returns:
        DataFrame with feature, outlier_count, outlier_pct per feature.
    """
    records = []
    for col in feature_cols:
        if col not in df.columns:
            continue
        series = df[col].dropna()
        if series.empty or series.std() == 0:
            records.append({"feature": col, "outlier_count": 0, "outlier_pct": 0.0})
            continue

        z_scores = np.abs((series - series.mean()) / series.std())
        outlier_count = int((z_scores > threshold).sum())
        records.append({
            "feature": col,
            "outlier_count": outlier_count,
            "outlier_pct": round(outlier_count / len(series) * 100, 2),
        })
    return pd.DataFrame(records).sort_values("outlier_pct", ascending=False)


def run_eda(engine: Engine, ticker: str = "AAPL") -> dict[str, object]:
    """Run comprehensive EDA on a ticker's training data.

    Args:
        engine: SQLAlchemy sync engine.
        ticker: Stock ticker to analyze.

    Returns:
        Dict with all analysis results.
    """
    logger.info("Running EDA for %s...", ticker)

    df = load_training_data(engine, ticker)
    if df.empty:
        return {"status": "no_data", "ticker": ticker}

    feature_cols = get_feature_columns()

    report = {
        "status": "success",
        "ticker": ticker,
        "total_rows": len(df),
        "date_range": {
            "start": str(df["timestamp"].min()),
            "end": str(df["timestamp"].max()),
        },
        "missing_values": analyze_missing_values(df).to_dict(orient="records"),
        "duplicates": analyze_duplicates(df),
        "class_balance": analyze_class_balance(df),
        "feature_distributions": analyze_feature_distributions(df, feature_cols).to_dict(orient="records"),
        "correlations": analyze_correlations(df, feature_cols),
        "outliers": analyze_outliers(df, feature_cols).to_dict(orient="records"),
    }

    # Print summary
    _print_eda_summary(report)

    return report


def _print_eda_summary(report: dict[str, object]) -> None:
    """Pretty-print the EDA summary to console."""
    print("\n" + "=" * 60)
    print(f"  EDA Report: {report['ticker']}")
    print("=" * 60)

    print(f"\n  Total rows: {report['total_rows']}")
    print(f"  Date range: {report['date_range']['start']} to {report['date_range']['end']}")

    # Missing values
    print("\n  --- Missing Values ---")
    missing = report["missing_values"]
    has_missing = False
    for m in missing:
        if m["missing_count"] > 0:
            print(f"    {m['column']}: {m['missing_count']} ({m['missing_pct']}%)")
            has_missing = True
    if not has_missing:
        print("    No missing values found!")

    # Duplicates
    dupes = report["duplicates"]
    print(f"\n  --- Duplicates ---")
    print(f"    Duplicate rows: {dupes['duplicate_rows']} ({dupes['duplicate_pct']}%)")

    # Class balance
    balance = report["class_balance"]
    print(f"\n  --- Class Balance ---")
    print(f"    UP days: {balance['up_days']} ({balance['up_pct']}%)")
    print(f"    DOWN days: {balance['down_days']} ({balance['down_pct']}%)")
    print(f"    Balance ratio: {balance['balance_ratio']}")
    print(f"    Balanced: {'Yes' if balance['is_balanced'] else 'No (consider resampling)'}")

    # Feature distributions
    print(f"\n  --- Feature Distributions ---")
    for feat in report["feature_distributions"]:
        skew_flag = " âš ï¸ SKEWED" if abs(feat["skewness"]) > 2 else ""
        print(f"    {feat['feature']:20s} | mean={feat['mean']:10.4f} std={feat['std']:10.4f} "
              f"skew={feat['skewness']:6.2f}{skew_flag}")

    # High correlations
    high_corr = report["correlations"]["high_correlation_pairs"]
    print(f"\n  --- Highly Correlated Features (|r| > 0.8) ---")
    if high_corr:
        for pair in high_corr:
            print(f"    {pair['feature_1']} <-> {pair['feature_2']}: r={pair['correlation']}")
    else:
        print("    No highly correlated feature pairs found")

    # Target correlations
    target_corrs = report["correlations"]["target_correlations"]
    if target_corrs:
        print(f"\n  --- Feature-Target Correlations ---")
        sorted_corrs = sorted(target_corrs.items(), key=lambda x: abs(x[1]), reverse=True)
        for feat, corr in sorted_corrs:
            strength = "STRONG" if abs(corr) > 0.1 else "weak"
            print(f"    {feat:20s}: r={corr:+.4f} ({strength})")

    # Outliers
    print(f"\n  --- Outliers (z > 3.0) ---")
    for o in report["outliers"]:
        if o["outlier_count"] > 0:
            print(f"    {o['feature']:20s}: {o['outlier_count']} outliers ({o['outlier_pct']}%)")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    from sqlalchemy import create_engine
    from src.config import settings

    sync_engine = create_engine(settings.database_url_sync)
    report = run_eda(sync_engine, ticker="AAPL")
