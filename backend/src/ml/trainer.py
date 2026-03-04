"""ML model training with walk-forward validation.

Trains classification models to predict next-day stock price direction
(up/down) using technical indicators and lag features. Implements
walk-forward validation to prevent data leakage in time-series data.
"""

import logging
import os
import pickle
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score
from sqlalchemy import text
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)

# Walk-forward parameters
TRAIN_WINDOW = 252  # 1 year of trading days
TEST_WINDOW = 21    # 1 month of trading days

# Feature columns from technical_indicators
FEATURE_COLUMNS = [
    "rsi_14", "macd", "macd_signal",
    "bollinger_upper", "bollinger_lower",
    "sma_50", "sma_200",
]


def load_training_data(engine: Engine, ticker: str) -> pd.DataFrame:
    """Load and prepare training data for a single ticker.

    Joins raw_prices with technical_indicators and computes the target
    variable (next-day direction) and additional lag features.

    Args:
        engine: SQLAlchemy sync engine.
        ticker: Stock ticker symbol.

    Returns:
        DataFrame with features and target column, sorted by timestamp.
    """
    query = text("""
        SELECT
            rp.timestamp,
            rp.close,
            ti.rsi_14, ti.macd, ti.macd_signal,
            ti.bollinger_upper, ti.bollinger_lower,
            ti.sma_50, ti.sma_200
        FROM raw_prices rp
        INNER JOIN technical_indicators ti
            ON rp.ticker = ti.ticker AND rp.timestamp = ti.timestamp
        WHERE rp.ticker = :ticker
        ORDER BY rp.timestamp ASC
    """)

    with engine.connect() as conn:
        result = conn.execute(query, {"ticker": ticker})
        rows = result.fetchall()

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(
        rows,
        columns=["timestamp", "close", *FEATURE_COLUMNS],
    )

    # Convert types
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    for col in ["close", *FEATURE_COLUMNS]:
        df[col] = df[col].astype(float)

    # Compute lag return features
    df["return_1d"] = df["close"].pct_change(1)
    df["return_3d"] = df["close"].pct_change(3)
    df["return_5d"] = df["close"].pct_change(5)

    # Compute rolling volatility (20-day)
    df["volatility_20d"] = np.log(df["close"] / df["close"].shift(1)).rolling(20).std() * np.sqrt(252)

    # Target: next-day direction (1 = up, 0 = down)
    df["target"] = (df["close"].shift(-1) > df["close"]).astype(int)

    # Drop rows with NaN (warmup + last row with no target)
    df = df.dropna().reset_index(drop=True)

    return df


def walk_forward_split(
    df: pd.DataFrame,
    train_window: int = TRAIN_WINDOW,
    test_window: int = TEST_WINDOW,
) -> list[tuple[pd.DataFrame, pd.DataFrame]]:
    """Generate walk-forward train/test splits.

    NEVER shuffles data â€” preserves temporal ordering.

    Args:
        df: Full dataset sorted by timestamp.
        train_window: Number of rows in each training window.
        test_window: Number of rows in each test window.

    Returns:
        List of (train_df, test_df) tuples.
    """
    splits: list[tuple[pd.DataFrame, pd.DataFrame]] = []
    start = 0

    while start + train_window + test_window <= len(df):
        train = df.iloc[start : start + train_window]
        test = df.iloc[start + train_window : start + train_window + test_window]
        splits.append((train, test))
        start += test_window

    logger.info("Generated %d walk-forward splits", len(splits))
    return splits


def get_feature_columns() -> list[str]:
    """Return the full list of feature column names."""
    return FEATURE_COLUMNS + ["return_1d", "return_3d", "return_5d", "volatility_20d"]


def evaluate_model(y_true: np.ndarray, y_pred: np.ndarray, y_prob: np.ndarray) -> dict[str, float]:
    """Compute classification metrics.

    Args:
        y_true: True labels.
        y_pred: Predicted labels.
        y_prob: Predicted probabilities for the positive class.

    Returns:
        Dict with accuracy, precision, recall, f1, and auc_roc.
    """
    return {
        "accuracy": accuracy_score(y_true, y_pred),
        "precision": precision_score(y_true, y_pred, zero_division=0),
        "recall": recall_score(y_true, y_pred, zero_division=0),
        "f1": f1_score(y_true, y_pred, zero_division=0),
        "auc_roc": roc_auc_score(y_true, y_prob) if len(np.unique(y_true)) > 1 else 0.5,
    }


def train_logistic_regression(X_train: np.ndarray, y_train: np.ndarray) -> LogisticRegression:
    """Train a logistic regression model."""
    model = LogisticRegression(max_iter=1000, random_state=42, C=1.0)
    model.fit(X_train, y_train)
    return model


def train_random_forest(X_train: np.ndarray, y_train: np.ndarray) -> RandomForestClassifier:
    """Train a random forest classifier."""
    model = RandomForestClassifier(
        n_estimators=100, max_depth=10, min_samples_leaf=5,
        random_state=42, n_jobs=-1,
    )
    model.fit(X_train, y_train)
    return model


def train_xgboost(X_train: np.ndarray, y_train: np.ndarray, use_optuna: bool = True) -> object:
    """Train an XGBoost classifier, optionally with Optuna tuning.

    Args:
        X_train: Training features.
        y_train: Training labels.
        use_optuna: Whether to use Optuna for hyperparameter tuning.

    Returns:
        Trained XGBClassifier.
    """
    import xgboost as xgb

    if not use_optuna:
        model = xgb.XGBClassifier(
            n_estimators=100, max_depth=6, learning_rate=0.1,
            random_state=42, eval_metric="logloss", verbosity=0,
        )
        model.fit(X_train, y_train)
        return model

    import optuna
    optuna.logging.set_verbosity(optuna.logging.WARNING)

    def objective(trial: optuna.Trial) -> float:
        params = {
            "n_estimators": trial.suggest_int("n_estimators", 50, 300),
            "max_depth": trial.suggest_int("max_depth", 3, 10),
            "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
            "subsample": trial.suggest_float("subsample", 0.6, 1.0),
            "colsample_bytree": trial.suggest_float("colsample_bytree", 0.6, 1.0),
            "min_child_weight": trial.suggest_int("min_child_weight", 1, 10),
            "gamma": trial.suggest_float("gamma", 0.0, 5.0),
            "random_state": 42,
            "eval_metric": "logloss",
            "verbosity": 0,
        }
        model = xgb.XGBClassifier(**params)
        model.fit(X_train, y_train)
        preds = model.predict(X_train)
        return f1_score(y_train, preds, zero_division=0)

    study = optuna.create_study(direction="maximize")
    study.optimize(objective, n_trials=50, show_progress_bar=False)

    best_params = study.best_params
    best_params.update({"random_state": 42, "eval_metric": "logloss", "verbosity": 0})
    logger.info("Best XGBoost params (F1=%.4f): %s", study.best_value, best_params)

    model = xgb.XGBClassifier(**best_params)
    model.fit(X_train, y_train)
    return model


def run_training_pipeline(
    engine: Engine,
    ticker: str = "AAPL",
    model_dir: str = "./models",
    use_optuna: bool = True,
    run_eda_report: bool = True,
) -> dict[str, object]:
    """Run the full training pipeline for a single ticker.

    Pipeline steps:
    1. Load raw training data
    2. Run EDA report (optional)
    3. Generate data quality report
    4. Walk-forward split
    5. For each fold: prepare data (clean, scale) â†’ train 3 models â†’ evaluate
    6. Select best model by F1, save to disk

    Args:
        engine: SQLAlchemy sync engine.
        ticker: Stock ticker to train on.
        model_dir: Directory to save model artifacts.
        use_optuna: Whether to use Optuna for XGBoost tuning.
        run_eda_report: Whether to run and print EDA report.

    Returns:
        Dict with training results including best model info and metrics.
    """
    from src.ml.data_prep import generate_quality_report, prepare_split

    logger.info("Starting training pipeline for %s", ticker)

    # Step 1: Load data
    df = load_training_data(engine, ticker)
    if df.empty or len(df) < TRAIN_WINDOW + TEST_WINDOW:
        logger.warning("Insufficient data for %s (%d rows)", ticker, len(df))
        return {"status": "insufficient_data", "rows": len(df)}

    feature_cols = get_feature_columns()

    # Step 2: Run EDA
    if run_eda_report:
        from src.ml.eda import run_eda
        eda_report = run_eda(engine, ticker)
    else:
        eda_report = None

    # Step 3: Data quality report
    quality_report = generate_quality_report(df, feature_cols)
    if quality_report.warnings:
        logger.info("Data quality warnings:")
        for w in quality_report.warnings:
            logger.warning("  %s", w)
    else:
        logger.info("Data quality: no issues found")

    logger.info(
        "Data quality summary: %d rows, %d missing values, %d duplicates, %d infinite values",
        quality_report.original_rows,
        quality_report.missing_values_found,
        quality_report.duplicates_removed,
        quality_report.infinite_values_fixed,
    )

    # Step 4: Walk-forward splits
    splits = walk_forward_split(df)
    if not splits:
        logger.warning("No valid splits for %s", ticker)
        return {"status": "no_splits"}

    model_configs = {
        "logistic_regression": train_logistic_regression,
        "random_forest": train_random_forest,
        "xgboost": lambda X, y: train_xgboost(X, y, use_optuna=use_optuna),
    }

    all_results: dict[str, list[dict[str, float]]] = {name: [] for name in model_configs}
    best_models: dict[str, object] = {}
    scalers: dict[str, object] = {}

    # Step 5: Train and evaluate per fold
    for fold_idx, (train_df, test_df) in enumerate(splits):
        logger.info("Processing fold %d/%d...", fold_idx + 1, len(splits))

        # Prepare data: clean, handle missing/inf, cap outliers, scale
        prepared = prepare_split(
            train_df, test_df,
            feature_cols=feature_cols,
            target_col="target",
            cap_outliers_enabled=True,
            scale_enabled=True,
        )

        if prepared.imputed_values_train > 0:
            logger.info(
                "Fold %d: imputed %d values in train, %d in test",
                fold_idx, prepared.imputed_values_train, prepared.imputed_values_test,
            )

        for model_name, train_fn in model_configs.items():
            model = train_fn(prepared.X_train, prepared.y_train)
            y_pred = model.predict(prepared.X_test)
            y_prob = model.predict_proba(prepared.X_test)[:, 1]

            metrics = evaluate_model(prepared.y_test, y_pred, y_prob)
            all_results[model_name].append(metrics)
            best_models[model_name] = model
            scalers[model_name] = prepared.scaler

            logger.debug(
                "Fold %d | %s | F1=%.4f Acc=%.4f",
                fold_idx, model_name, metrics["f1"], metrics["accuracy"],
            )

    # Step 6: Compute average metrics and select best
    avg_metrics: dict[str, dict[str, float]] = {}
    for model_name, fold_results in all_results.items():
        avg = {
            metric: float(np.mean([r[metric] for r in fold_results]))
            for metric in fold_results[0]
        }
        avg_metrics[model_name] = avg
        logger.info(
            "%s avg metrics: F1=%.4f Acc=%.4f Prec=%.4f Rec=%.4f AUC=%.4f",
            model_name, avg["f1"], avg["accuracy"],
            avg["precision"], avg["recall"], avg["auc_roc"],
        )

    best_name = max(avg_metrics, key=lambda k: avg_metrics[k]["f1"])
    best_metric = avg_metrics[best_name]
    best_model = best_models[best_name]
    best_scaler = scalers[best_name]

    logger.info("Best model: %s (F1=%.4f)", best_name, best_metric["f1"])

    # Save model and scaler together
    Path(model_dir).mkdir(parents=True, exist_ok=True)
    version = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    model_filename = f"{best_name}_{ticker}_{version}.pkl"
    model_path = os.path.join(model_dir, model_filename)

    with open(model_path, "wb") as f:
        pickle.dump({"model": best_model, "scaler": best_scaler, "feature_columns": feature_cols}, f)

    logger.info("Saved best model + scaler to %s", model_path)

    return {
        "status": "success",
        "ticker": ticker,
        "best_model_name": best_name,
        "version": version,
        "model_path": model_path,
        "metrics": best_metric,
        "all_metrics": avg_metrics,
        "num_folds": len(splits),
        "feature_columns": feature_cols,
        "data_quality": {
            "original_rows": quality_report.original_rows,
            "missing_values": quality_report.missing_values_found,
            "duplicates": quality_report.duplicates_removed,
            "infinite_values": quality_report.infinite_values_fixed,
            "warnings": quality_report.warnings,
        },
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    from sqlalchemy import create_engine
    from src.config import settings

    sync_engine = create_engine(settings.database_url_sync)
    result = run_training_pipeline(sync_engine, ticker="AAPL", use_optuna=True)

    print("\nTraining Results:")
    print("-" * 50)
    if result["status"] == "success":
        print(f"  Best model: {result['best_model_name']}")
        print(f"  Version: {result['version']}")
        print(f"  Folds: {result['num_folds']}")
        for name, metrics in result["all_metrics"].items():
            print(f"\n  {name}:")
            for k, v in metrics.items():
                print(f"    {k}: {v:.4f}")
    else:
        print(f"  Status: {result['status']}")
