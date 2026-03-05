"""Integration tests for the FinSense API endpoints."""

import pytest
from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


class TestHealthEndpoint:

    def test_health_returns_200(self) -> None:
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ("ok", "degraded")
        assert "database" in data
        assert "timestamp" in data


class TestStocksEndpoints:

    def test_list_stocks(self) -> None:
        response = client.get("/api/v1/stocks")
        assert response.status_code == 200
        data = response.json()
        assert "stocks" in data
        assert "count" in data
        assert data["count"] > 0
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
        response = client.get("/api/v1/stocks/AAPL")
        assert response.status_code == 200
        data = response.json()
        assert data["ticker"] == "AAPL"
        assert "latest_price" in data
        assert "change_pct" in data
        assert "technical_indicators" in data

    def test_get_stock_detail_case_insensitive(self) -> None:
        response = client.get("/api/v1/stocks/aapl")
        assert response.status_code == 200
        assert response.json()["ticker"] == "AAPL"

    def test_get_stock_detail_not_found(self) -> None:
        response = client.get("/api/v1/stocks/ZZZZZ")
        assert response.status_code == 404

    def test_get_stock_history(self) -> None:
        response = client.get("/api/v1/stocks/AAPL/history?page=1&page_size=10")
        assert response.status_code == 200
        data = response.json()
        assert data["ticker"] == "AAPL"
        assert len(data["data"]) <= 10
        assert data["page"] == 1

    def test_get_stock_history_not_found(self) -> None:
        response = client.get("/api/v1/stocks/ZZZZZ/history")
        assert response.status_code == 404


class TestPipelineEndpoint:

    def test_pipeline_status(self) -> None:
        response = client.get("/api/v1/pipeline-status")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ("healthy", "degraded", "failed")
        assert "row_counts" in data
        assert "message" in data


class TestPortfolioEndpoint:

    def test_portfolio_risk(self) -> None:
        response = client.get(
            "/api/v1/portfolio-risk",
            params={"tickers": "AAPL,MSFT", "weights": "0.6,0.4"},
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
        response = client.get(
            "/api/v1/portfolio-risk",
            params={"tickers": "AAPL,MSFT", "weights": "0.3,0.3"},
        )
        assert response.status_code == 400
        assert "sum to 1.0" in response.json()["detail"]

    def test_portfolio_risk_mismatched_lengths(self) -> None:
        response = client.get(
            "/api/v1/portfolio-risk",
            params={"tickers": "AAPL,MSFT,GOOGL", "weights": "0.5,0.5"},
        )
        assert response.status_code == 400

    def test_portfolio_risk_invalid_ticker(self) -> None:
        response = client.get(
            "/api/v1/portfolio-risk",
            params={"tickers": "ZZZZZ", "weights": "1.0"},
        )
        assert response.status_code == 404


class TestPredictEndpoint:

    def test_predict_returns_prediction(self) -> None:
        response = client.post("/api/v1/predict", json={"ticker": "AAPL"})
        # May fail if model not loaded in test env, but should not 500
        assert response.status_code in (200, 400)
        if response.status_code == 200:
            data = response.json()
            assert data["ticker"] == "AAPL"
            assert data["direction"] in ("UP", "DOWN")
            assert 0.0 <= data["confidence"] <= 1.0

    def test_predict_invalid_ticker(self) -> None:
        response = client.post("/api/v1/predict", json={"ticker": ""})
        assert response.status_code == 422  # Validation error
