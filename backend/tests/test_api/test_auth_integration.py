"""Integration-style tests for API key enforcement on protected routes."""

from unittest.mock import patch
from typing import Any

import pytest
from fastapi.testclient import TestClient

from src.api.main import app  # type: ignore[import-untyped]

client = TestClient(app)
pytestmark = pytest.mark.integration


class TestProtectedRoutesApiKey:

    def test_predict_requires_api_key_when_enabled(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("src.api.dependencies.settings.api_require_key", True)
        monkeypatch.setattr("src.api.dependencies.settings.api_key", "secret")

        response = client.post("/api/v1/predict", json={"ticker": "AAPL"})
        assert response.status_code == 401

    def test_portfolio_requires_api_key_when_enabled(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("src.api.dependencies.settings.api_require_key", True)
        monkeypatch.setattr("src.api.dependencies.settings.api_key", "secret")

        response = client.get(
            "/api/v1/portfolio-risk",
            params={"tickers": "AAPL,MSFT", "weights": "0.5,0.5"},
        )
        assert response.status_code == 401

    def test_predict_with_valid_api_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("src.api.dependencies.settings.api_require_key", True)
        monkeypatch.setattr("src.api.dependencies.settings.api_key", "secret")

        fake_result: dict[str, Any] = {
            "ticker": "AAPL",
            "direction": "UP",
            "confidence": 0.77,
            "model_version": "v-test",
            "model_name": "test-model",
            "timestamp": "2026-03-10T00:00:00+00:00",
        }

        with patch("src.api.routes.predict.predict", return_value=fake_result):
            response = client.post(
                "/api/v1/predict",
                json={"ticker": "AAPL"},
                headers={"x-api-key": "secret"},
            )

        assert response.status_code == 200
        body = response.json()
        assert body["ticker"] == "AAPL"
        assert body["direction"] == "UP"

    def test_portfolio_with_valid_api_key_reaches_endpoint(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("src.api.dependencies.settings.api_require_key", True)
        monkeypatch.setattr("src.api.dependencies.settings.api_key", "secret")

        # Invalid weights should fail endpoint validation after auth passes.
        response = client.get(
            "/api/v1/portfolio-risk",
            params={"tickers": "AAPL,MSFT", "weights": "0.2,0.2"},
            headers={"x-api-key": "secret"},
        )
        assert response.status_code == 400
