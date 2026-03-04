"""Data preparation module for ML training.

Handles feature scaling, missing value imputation, outlier treatment,
and train/test data preparation. Ensures data is clean and properly
formatted before being fed to ML models.
"""

import logging
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)


@dataclass
class PreparedData:
    """Container for prepared training/test data."""

    X_train: np.ndarray
    y_train: np.ndarray
    X_test: np.ndarray
    y_test: np.ndarray
    scaler: StandardScaler
    feature_names: list[str]
    dropped_rows_train: int = 0
    dropped_rows_test: int = 0
    imputed_values_train: int = 0
    imputed_values_test: int = 0


@dataclass
class DataQualityReport:
    """Summary of data quality issues found and fixed."""

    original_rows: int = 0
    final_rows: int = 0
    missing_values_found: int = 0
    missing_values_imputed: int = 0
    duplicates_removed: int = 0
    outliers_capped: int = 0
    infinite_values_fixed: int = 0
    warnings: list[str] = field(default_factory=list)


def handle_missing_values(
    df: pd.DataFrame,
    feature_cols: list[str],
    strategy: str = "median",
) -> tuple[pd.DataFrame, int]:
    """Handle missing values in feature columns.

    Args:
        df: Input DataFrame.
        feature_cols: Columns to check for missing values.
        strategy: Imputation strategy - "median", "mean", or "drop".

    Returns:
        Tuple of (cleaned DataFrame, number of values imputed/rows dropped).
    """
    total_imputed = 0

    if strategy == "drop":
        before = len(df)
        df = df.dropna(subset=feature_cols).copy()
        return df, before - len(df)

    for col in feature_cols:
        if col not in df.columns:
            continue
        missing_count = int(df[col].isna().sum())
        if missing_count > 0:
            if strategy == "median":
                fill_value = df[col].median()
            elif strategy == "mean":
                fill_value = df[col].mean()
            else:
                fill_value = 0.0

            df[col] = df[col].fillna(fill_value)
            total_imputed += missing_count
            logger.info(
                "Imputed %d missing values in '%s' with %s (%.4f)",
                missing_count, col, strategy, fill_value,
            )

    return df, total_imputed


def handle_infinite_values(df: pd.DataFrame, feature_cols: list[str]) -> tuple[pd.DataFrame, int]:
    """Replace infinite values with NaN, then forward-fill.

    Args:
        df: Input DataFrame.
        feature_cols: Columns to check.

    Returns:
        Tuple of (cleaned DataFrame, number of infinite values replaced).
    """
    total_fixed = 0
    for col in feature_cols:
        if col not in df.columns:
            continue
        inf_mask = np.isinf(df[col])
        inf_count = int(inf_mask.sum())
        if inf_count > 0:
            df[col] = df[col].replace([np.inf, -np.inf], np.nan)
            df[col] = df[col].ffill().bfill()
            total_fixed += inf_count
            logger.info("Fixed %d infinite values in '%s'", inf_count, col)

    return df, total_fixed


def cap_outliers(
    df: pd.DataFrame,
    feature_cols: list[str],
    method: str = "iqr",
    threshold: float = 1.5,
) -> tuple[pd.DataFrame, int]:
    """Cap outlier values using IQR or z-score method.

    Args:
        df: Input DataFrame.
        feature_cols: Columns to check.
        method: "iqr" for interquartile range, "zscore" for z-score.
        threshold: IQR multiplier (default 1.5) or z-score threshold (default 3.0).

    Returns:
        Tuple of (cleaned DataFrame, number of values capped).
    """
    total_capped = 0

    for col in feature_cols:
        if col not in df.columns:
            continue

        series = df[col]

        if method == "iqr":
            q1 = series.quantile(0.25)
            q3 = series.quantile(0.75)
            iqr = q3 - q1
            lower = q1 - threshold * iqr
            upper = q3 + threshold * iqr
        elif method == "zscore":
            mean = series.mean()
            std = series.std()
            if std == 0:
                continue
            lower = mean - threshold * std
            upper = mean + threshold * std
        else:
            continue

        capped_lower = int((series < lower).sum())
        capped_upper = int((series > upper).sum())
        capped = capped_lower + capped_upper

        if capped > 0:
            df[col] = series.clip(lower=lower, upper=upper)
            total_capped += capped
            logger.info(
                "Capped %d outliers in '%s' (lower=%.4f, upper=%.4f)",
                capped, col, lower, upper,
            )

    return df, total_capped


def remove_duplicates(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Remove duplicate rows.

    Returns:
        Tuple of (deduplicated DataFrame, number of duplicates removed).
    """
    before = len(df)
    df = df.drop_duplicates().reset_index(drop=True)
    removed = before - len(df)
    if removed > 0:
        logger.info("Removed %d duplicate rows", removed)
    return df, removed


def scale_features(
    X_train: np.ndarray,
    X_test: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, StandardScaler]:
    """Apply StandardScaler to features.

    Fits on training data only, transforms both train and test.
    This prevents data leakage from test set statistics.

    Args:
        X_train: Training feature matrix.
        X_test: Test feature matrix.

    Returns:
        Tuple of (scaled_X_train, scaled_X_test, fitted_scaler).
    """
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    logger.info(
        "Scaled features: %d train samples, %d test samples, %d features",
        X_train_scaled.shape[0], X_test_scaled.shape[0], X_train_scaled.shape[1],
    )
    return X_train_scaled, X_test_scaled, scaler


def prepare_split(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    feature_cols: list[str],
    target_col: str = "target",
    cap_outliers_enabled: bool = True,
    scale_enabled: bool = True,
) -> PreparedData:
    """Full data preparation pipeline for a single train/test split.

    Steps:
    1. Handle infinite values
    2. Handle missing values (median imputation)
    3. Remove duplicates
    4. Cap outliers (IQR method, training set only â€” apply same bounds to test)
    5. Scale features (fit on train, transform both)

    Args:
        train_df: Training DataFrame.
        test_df: Test DataFrame.
        feature_cols: List of feature column names.
        target_col: Name of the target column.
        cap_outliers_enabled: Whether to cap outliers.
        scale_enabled: Whether to apply StandardScaler.

    Returns:
        PreparedData with cleaned, scaled arrays and metadata.
    """
    train = train_df.copy()
    test = test_df.copy()

    # Step 1: Handle infinite values
    train, inf_train = handle_infinite_values(train, feature_cols)
    test, inf_test = handle_infinite_values(test, feature_cols)

    # Step 2: Handle missing values
    train, imputed_train = handle_missing_values(train, feature_cols, strategy="median")
    test, imputed_test = handle_missing_values(test, feature_cols, strategy="median")

    # Step 3: Remove duplicates
    train, dupes_train = remove_duplicates(train)

    # Step 4: Cap outliers (only on training data bounds)
    capped = 0
    if cap_outliers_enabled:
        train, capped = cap_outliers(train, feature_cols, method="iqr", threshold=1.5)
        # Apply same bounds to test set
        for col in feature_cols:
            if col in train.columns and col in test.columns:
                col_min = train[col].min()
                col_max = train[col].max()
                test[col] = test[col].clip(lower=col_min, upper=col_max)

    # Extract arrays
    X_train = train[feature_cols].values.astype(np.float64)
    y_train = train[target_col].values.astype(np.int64)
    X_test = test[feature_cols].values.astype(np.float64)
    y_test = test[target_col].values.astype(np.int64)

    # Step 5: Scale features
    scaler = StandardScaler()
    if scale_enabled:
        X_train, X_test, scaler = scale_features(X_train, X_test)

    return PreparedData(
        X_train=X_train,
        y_train=y_train,
        X_test=X_test,
        y_test=y_test,
        scaler=scaler,
        feature_names=feature_cols,
        dropped_rows_train=dupes_train,
        dropped_rows_test=0,
        imputed_values_train=imputed_train + inf_train,
        imputed_values_test=imputed_test + inf_test,
    )


def generate_quality_report(
    df: pd.DataFrame,
    feature_cols: list[str],
) -> DataQualityReport:
    """Generate a data quality summary report.

    Args:
        df: Raw DataFrame before preparation.
        feature_cols: Feature columns to analyze.

    Returns:
        DataQualityReport with counts of issues found.
    """
    report = DataQualityReport(original_rows=len(df))
    warnings = []

    # Missing values
    for col in feature_cols:
        if col in df.columns:
            missing = int(df[col].isna().sum())
            report.missing_values_found += missing
            if missing > 0:
                pct = missing / len(df) * 100
                warnings.append(f"'{col}' has {missing} missing values ({pct:.1f}%)")

    # Duplicates
    report.duplicates_removed = int(df.duplicated().sum())
    if report.duplicates_removed > 0:
        warnings.append(f"{report.duplicates_removed} duplicate rows found")

    # Infinite values
    for col in feature_cols:
        if col in df.columns:
            inf_count = int(np.isinf(df[col]).sum())
            report.infinite_values_fixed += inf_count
            if inf_count > 0:
                warnings.append(f"'{col}' has {inf_count} infinite values")

    # Class balance check
    if "target" in df.columns:
        balance = df["target"].value_counts(normalize=True)
        minority_pct = balance.min() * 100
        if minority_pct < 30:
            warnings.append(
                f"Class imbalance detected: minority class is {minority_pct:.1f}%"
            )

    report.final_rows = len(df) - report.duplicates_removed
    report.warnings = warnings

    return report
