"""Tests for ML training, registry, and prediction modules."""

import numpy as np
import pandas as pd
import pytest
from unittest.mock import MagicMock, patch

from src.ml.trainer import (
    walk_forward_split,
    evaluate_model,
    get_feature_columns,
    TRAIN_WINDOW,
    TEST_WINDOW,
)


class TestWalkForwardSplit:

    def test_correct_number_of_splits(self) -> None:
        """Should generate the right number of splits."""
        n_rows = TRAIN_WINDOW + TEST_WINDOW * 3  # Enough for 3 folds
        df = pd.DataFrame({"x": range(n_rows)})
        splits = walk_forward_split(df)
        assert len(splits) == 3

    def test_no_splits_when_insufficient_data(self) -> None:
        """Should return empty list when data is too small."""
        df = pd.DataFrame({"x": range(100)})
        splits = walk_forward_split(df)
        assert len(splits) == 0

    def test_train_test_sizes(self) -> None:
        """Each split should have correct train and test sizes."""
        n_rows = TRAIN_WINDOW + TEST_WINDOW * 2
        df = pd.DataFrame({"x": range(n_rows)})
        splits = walk_forward_split(df)

        for train, test in splits:
            assert len(train) == TRAIN_WINDOW
            assert len(test) == TEST_WINDOW

    def test_no_overlap_between_train_and_test(self) -> None:
        """Train and test sets should not overlap within a fold."""
        n_rows = TRAIN_WINDOW + TEST_WINDOW * 2
        df = pd.DataFrame({"x": range(n_rows)})
        splits = walk_forward_split(df)

        for train, test in splits:
            train_indices = set(train.index)
            test_indices = set(test.index)
            assert train_indices.isdisjoint(test_indices)

    def test_test_always_after_train(self) -> None:
        """Test data should always come after training data (no leakage)."""
        n_rows = TRAIN_WINDOW + TEST_WINDOW * 2
        df = pd.DataFrame({"x": range(n_rows)})
        splits = walk_forward_split(df)

        for train, test in splits:
            assert train.index.max() < test.index.min()

    def test_sliding_window(self) -> None:
        """Second fold's train start should be TEST_WINDOW ahead of first."""
        n_rows = TRAIN_WINDOW + TEST_WINDOW * 3
        df = pd.DataFrame({"x": range(n_rows)})
        splits = walk_forward_split(df)

        assert splits[1][0].index[0] == splits[0][0].index[0] + TEST_WINDOW


class TestEvaluateModel:

    def test_perfect_predictions(self) -> None:
        y_true = np.array([1, 0, 1, 0, 1])
        y_pred = np.array([1, 0, 1, 0, 1])
        y_prob = np.array([0.9, 0.1, 0.9, 0.1, 0.9])

        metrics = evaluate_model(y_true, y_pred, y_prob)
        assert metrics["accuracy"] == 1.0
        assert metrics["f1"] == 1.0
        assert metrics["auc_roc"] == 1.0

    def test_worst_predictions(self) -> None:
        y_true = np.array([1, 0, 1, 0, 1])
        y_pred = np.array([0, 1, 0, 1, 0])
        y_prob = np.array([0.1, 0.9, 0.1, 0.9, 0.1])

        metrics = evaluate_model(y_true, y_pred, y_prob)
        assert metrics["accuracy"] == 0.0
        assert metrics["f1"] == 0.0

    def test_returns_all_metric_keys(self) -> None:
        y_true = np.array([1, 0, 1])
        y_pred = np.array([1, 0, 0])
        y_prob = np.array([0.8, 0.2, 0.4])

        metrics = evaluate_model(y_true, y_pred, y_prob)
        assert set(metrics.keys()) == {"accuracy", "precision", "recall", "f1", "auc_roc"}


class TestGetFeatureColumns:

    def test_returns_expected_count(self) -> None:
        """Should return 11 features (7 technical + 4 lag/vol)."""
        cols = get_feature_columns()
        assert len(cols) == 11

    def test_includes_technical_indicators(self) -> None:
        cols = get_feature_columns()
        assert "rsi_14" in cols
        assert "macd" in cols
        assert "sma_200" in cols

    def test_includes_lag_features(self) -> None:
        cols = get_feature_columns()
        assert "return_1d" in cols
        assert "return_5d" in cols
        assert "volatility_20d" in cols


class TestModelRegistry:

    def test_register_model(self) -> None:
        """Should insert model into registry and return ID."""
        from src.ml.registry import register_model

        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_conn.execute.return_value.scalar.return_value = 1
        mock_engine.begin.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_engine.begin.return_value.__exit__ = MagicMock(return_value=False)

        model_id = register_model(
            mock_engine,
            model_name="xgboost",
            version="20240102_153000",
            metrics={"accuracy": 0.58, "precision": 0.60, "recall": 0.55, "f1": 0.57},
            model_path="./models/xgboost_AAPL_20240102.pkl",
        )
        assert model_id == 1
        mock_conn.execute.assert_called_once()

    def test_promote_model(self) -> None:
        """Should deactivate all models then activate the specified one."""
        from src.ml.registry import promote_model

        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_conn.execute.return_value = mock_result
        mock_engine.begin.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_engine.begin.return_value.__exit__ = MagicMock(return_value=False)

        result = promote_model(mock_engine, "20240102_153000")
        assert result is True
        assert mock_conn.execute.call_count == 2  # deactivate all + activate one

    def test_promote_nonexistent_version(self) -> None:
        """Should return False for non-existent version."""
        from src.ml.registry import promote_model

        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_deactivate = MagicMock()
        mock_activate = MagicMock()
        mock_activate.rowcount = 0  # No rows updated
        mock_conn.execute.side_effect = [mock_deactivate, mock_activate]
        mock_engine.begin.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_engine.begin.return_value.__exit__ = MagicMock(return_value=False)

        result = promote_model(mock_engine, "nonexistent")
        assert result is False
