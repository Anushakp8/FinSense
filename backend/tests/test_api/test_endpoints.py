"""Integration tests for the FinSense API endpoints."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from src.api.dependencies import get_engine
from src.api.main import app

client = TestClient(app)
pytestmark = pytest.mark.integration


def _database_available() -> bool:
    try:
        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


DB_AVAILABLE = _database_available()


def _available_tickers(min_count: int = 1) -> list[str]:
    try:
        response = client.get("/api/v1/stocks")
    except Exception as exc:  # pragma: no cover - environment-dependent path
        pytest.skip(f"Database-dependent test skipped: {exc}")
    assert response.status_code == 200
    data = response.json()
    if data.get("count", 0) < min_count:
        pytest.skip(f"Test requires at least {min_count} ticker(s) with data")
    return [stock["ticker"] for stock in data["stocks"]]


class TestHealthEndpoint:

    def test_health_returns_200(self) -> None:
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ("ok", "degraded")
        assert "database" in data
        assert "timestamp" in data


@pytest.mark.skipif(not DB_AVAILABLE, reason="PostgreSQL unavailable for integration tests")
class TestStocksEndpoints:

    def test_list_stocks(self) -> None:
        response = client.get("/api/v1/stocks")
        assert response.status_code == 200
        data = response.json()
        assert "stocks" in data
        assert "count" in data
        assert data["count"] >= 0
        assert data["count"] == len(data["stocks"])

    def test_list_stocks_has_expected_fields(self) -> None:
        response = client.get("/api/v1/stocks")
        data = response.json()
        if data["count"] > 0:
            stock = data["stocks"][0]
            assert "ticker" in stock
            assert "latest_price" in stock
            assert "change_pct" in stock
            assert "volume" in stock

    def test_get_stock_detail(self) -> None:
        ticker = _available_tickers(min_count=1)[0]
        response = client.get(f"/api/v1/stocks/{ticker}")
        assert response.status_code == 200
        data = response.json()
        assert data["ticker"] == ticker
        assert "latest_price" in data
        assert "change_pct" in data
        assert "technical_indicators" in data

    def test_get_stock_detail_case_insensitive(self) -> None:
        ticker = _available_tickers(min_count=1)[0]
        response = client.get(f"/api/v1/stocks/{ticker.lower()}")
        assert response.status_code == 200
        assert response.json()["ticker"] == ticker

    def test_get_stock_detail_not_found(self) -> None:
        response = client.get("/api/v1/stocks/ZZZZZ")
        assert response.status_code == 404

    def test_get_stock_history(self) -> None:
        ticker = _available_tickers(min_count=1)[0]
        response = client.get(f"/api/v1/stocks/{ticker}/history?page=1&page_size=10")
        assert response.status_code == 200
        data = response.json()
        assert data["ticker"] == ticker
        assert len(data["data"]) <= 10
        assert data["page"] == 1

    def test_get_stock_history_not_found(self) -> None:
        response = client.get("/api/v1/stocks/ZZZZZ/history")
        assert response.status_code == 404


@pytest.mark.skipif(not DB_AVAILABLE, reason="PostgreSQL unavailable for integration tests")
class TestPipelineEndpoint:

    def test_pipeline_status(self) -> None:
        response = client.get("/api/v1/pipeline-status")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ("healthy", "degraded", "failed")
        assert "row_counts" in data
        assert "message" in data


@pytest.mark.skipif(not DB_AVAILABLE, reason="PostgreSQL unavailable for integration tests")
class TestPortfolioEndpoint:

    def test_portfolio_risk(self) -> None:
        tickers = _available_tickers(min_count=2)
        response = client.get(
            "/api/v1/portfolio-risk",
            params={"tickers": f"{tickers[0]},{tickers[1]}", "weights": "0.6,0.4"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "var_95" in data
        assert "var_99" in data
        assert "expected_return" in data
        assert "max_drawdown" in data
        assert "individual_risks" in data
        assert len(data["individual_risks"]) == 2

    def test_portfolio_risk_weights_must_sum_to_1(self) -> None:
        tickers = _available_tickers(min_count=2)
        response = client.get(
            "/api/v1/portfolio-risk",
            params={"tickers": f"{tickers[0]},{tickers[1]}", "weights": "0.3,0.3"},
        )
        assert response.status_code == 400
        assert "sum to 1.0" in response.json()["detail"]

    def test_portfolio_risk_mismatched_lengths(self) -> None:
        tickers = _available_tickers(min_count=3)
        response = client.get(
            "/api/v1/portfolio-risk",
            params={"tickers": f"{tickers[0]},{tickers[1]},{tickers[2]}", "weights": "0.5,0.5"},
        )
        assert response.status_code == 400

    def test_portfolio_risk_invalid_ticker(self) -> None:
        response = client.get(
            "/api/v1/portfolio-risk",
            params={"tickers": "ZZZZZ", "weights": "1.0"},
        )
        assert response.status_code == 404


@pytest.mark.skipif(not DB_AVAILABLE, reason="PostgreSQL unavailable for integration tests")
class TestPredictEndpoint:

    def test_predict_returns_prediction(self) -> None:
        ticker = _available_tickers(min_count=1)[0]
        response = client.post("/api/v1/predict", json={"ticker": ticker})
        # May fail if model not loaded in test env, but should not 500
        assert response.status_code in (200, 400)
        if response.status_code == 200:
            data = response.json()
            assert data["ticker"] == ticker
            assert data["direction"] in ("UP", "DOWN")
            assert 0.0 <= data["confidence"] <= 1.0

    def test_predict_invalid_ticker(self) -> None:
        response = client.post("/api/v1/predict", json={"ticker": ""})
        assert response.status_code == 422  # Validation error
