"""Unit tests for prediction service behavior."""

from unittest.mock import MagicMock, patch

import numpy as np

from src.ml.predictor import predict


class TestPredictor:

    def test_predict_uses_saved_feature_order_and_scaler(self) -> None:
        engine = MagicMock()

        model = MagicMock()
        model.predict.return_value = np.array([1])
        model.predict_proba.return_value = np.array([[0.1, 0.9]])

        scaler = MagicMock()
        scaler.transform.return_value = np.array([[10.0, 20.0]])

        model_data = {
            "model": model,
            "scaler": scaler,
            "feature_columns": ["macd", "rsi_14"],
        }
        metadata = {"version": "v1", "model_name": "test_model"}

        with (
            patch("src.ml.predictor.get_active_model", return_value=(model_data, metadata)),
            patch("src.ml.predictor._get_latest_features", return_value={"rsi_14": 2.0, "macd": 1.0}),
        ):
            result = predict(engine, "AAPL", use_cache=False)

        scaler.transform.assert_called_once()
        scaled_input = scaler.transform.call_args[0][0]
        assert scaled_input.shape == (1, 2)
        assert float(scaled_input[0][0]) == 1.0
        assert float(scaled_input[0][1]) == 2.0

        model.predict.assert_called_once_with(scaler.transform.return_value)
        model.predict_proba.assert_called_once_with(scaler.transform.return_value)
        assert result["direction"] == "UP"
        assert result["model_version"] == "v1"

    def test_predict_legacy_model_without_scaler(self) -> None:
        engine = MagicMock()

        model = MagicMock()
        model.predict.return_value = np.array([0])
        model.predict_proba.return_value = np.array([[0.8, 0.2]])

        features = {
            "rsi_14": 10.0,
            "macd": 1.0,
            "macd_signal": 1.0,
            "bollinger_upper": 1.0,
            "bollinger_lower": 1.0,
            "sma_50": 1.0,
            "sma_200": 1.0,
            "return_1d": 0.01,
            "return_3d": 0.01,
            "return_5d": 0.01,
            "volatility_20d": 0.1,
        }

        metadata = {"version": "legacy", "model_name": "legacy_model"}
        with (
            patch("src.ml.predictor.get_active_model", return_value=(model, metadata)),
            patch("src.ml.predictor._get_latest_features", return_value=features),
        ):
            result = predict(engine, "MSFT", use_cache=False)

        model.predict.assert_called_once()
        model.predict_proba.assert_called_once()
        assert result["direction"] == "DOWN"
        assert result["model_name"] == "legacy_model"
