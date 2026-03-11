"""Integration tests for request-id and optional rate limiting middleware."""

from unittest.mock import patch
from typing import Any

import pytest
from fastapi.testclient import TestClient

from src.api import main as api_main  # type: ignore[import-untyped]

client = TestClient(api_main.app)
pytestmark = pytest.mark.integration


class TestSecurityMiddleware:

    def test_request_id_header_propagated(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("src.config.settings.api_rate_limit_enabled", False)
        api_main.clear_rate_limiter_state()
        api_main.clear_metrics_state()

        response = client.get("/health", headers={"x-request-id": "req-123"})
        assert response.status_code == 200
        assert response.headers.get("x-request-id") == "req-123"

    def test_request_id_header_present(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("src.config.settings.api_rate_limit_enabled", False)
        api_main.clear_rate_limiter_state()
        api_main.clear_metrics_state()

        response = client.get("/health")
        assert response.status_code == 200
        assert response.headers.get("x-request-id")

    def test_rate_limit_applies_to_sensitive_route(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("src.config.settings.api_rate_limit_enabled", True)
        monkeypatch.setattr("src.config.settings.api_rate_limit_use_redis", False)
        monkeypatch.setattr("src.config.settings.api_rate_limit_max_requests", 2)
        monkeypatch.setattr("src.config.settings.api_rate_limit_window_seconds", 60)
        monkeypatch.setattr("src.api.dependencies.settings.api_require_key", True)
        monkeypatch.setattr("src.api.dependencies.settings.api_key", "secret")
        api_main.clear_rate_limiter_state()
        api_main.clear_metrics_state()

        fake_result: dict[str, Any] = {
            "ticker": "AAPL",
            "direction": "UP",
            "confidence": 0.75,
            "model_version": "v-test",
            "model_name": "test-model",
            "timestamp": "2026-03-10T00:00:00+00:00",
        }

        with patch("src.api.routes.predict.predict", return_value=fake_result):
            headers = {"x-api-key": "secret", "x-forwarded-for": "10.0.0.1"}
            r1 = client.post("/api/v1/predict", json={"ticker": "AAPL"}, headers=headers)
            r2 = client.post("/api/v1/predict", json={"ticker": "AAPL"}, headers=headers)
            r3 = client.post("/api/v1/predict", json={"ticker": "AAPL"}, headers=headers)

        assert r1.status_code == 200
        assert r2.status_code == 200
        assert r3.status_code == 429

        metrics = client.get("/metrics")
        assert metrics.status_code == 200
        assert "finsense_rate_limited_total 1" in metrics.text
        assert "finsense_rate_limited_by_path_total{path=\"/api/v1/predict\"} 1" in metrics.text

    def test_rate_limit_not_applied_to_health(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("src.config.settings.api_rate_limit_enabled", True)
        monkeypatch.setattr("src.config.settings.api_rate_limit_use_redis", False)
        monkeypatch.setattr("src.config.settings.api_rate_limit_max_requests", 1)
        monkeypatch.setattr("src.config.settings.api_rate_limit_window_seconds", 60)
        api_main.clear_rate_limiter_state()
        api_main.clear_metrics_state()

        r1 = client.get("/health", headers={"x-forwarded-for": "10.0.0.2"})
        r2 = client.get("/health", headers={"x-forwarded-for": "10.0.0.2"})

        assert r1.status_code == 200
        assert r2.status_code == 200

    def test_rate_limit_uses_redis_backend_when_available(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        class FakeRedis:
            def __init__(self) -> None:
                self.counts: dict[str, int] = {}

            def incr(self, key: str) -> int:
                self.counts[key] = self.counts.get(key, 0) + 1
                return self.counts[key]

            def expire(self, key: str, _: int) -> bool:
                return True

        monkeypatch.setattr("src.config.settings.api_rate_limit_enabled", True)
        monkeypatch.setattr("src.config.settings.api_rate_limit_use_redis", True)
        monkeypatch.setattr("src.config.settings.api_rate_limit_max_requests", 2)
        monkeypatch.setattr("src.config.settings.api_rate_limit_window_seconds", 60)
        monkeypatch.setattr("src.api.dependencies.settings.api_require_key", True)
        monkeypatch.setattr("src.api.dependencies.settings.api_key", "secret")
        api_main.clear_rate_limiter_state()
        api_main.clear_metrics_state()

        fake_redis = FakeRedis()
        getattr(api_main, "set_rate_limit_redis_client_for_tests")(fake_redis)

        fake_result: dict[str, Any] = {
            "ticker": "AAPL",
            "direction": "UP",
            "confidence": 0.75,
            "model_version": "v-test",
            "model_name": "test-model",
            "timestamp": "2026-03-10T00:00:00+00:00",
        }

        try:
            with patch("src.api.routes.predict.predict", return_value=fake_result):
                headers = {"x-api-key": "secret", "x-forwarded-for": "10.0.0.10"}
                r1 = client.post("/api/v1/predict", json={"ticker": "AAPL"}, headers=headers)
                r2 = client.post("/api/v1/predict", json={"ticker": "AAPL"}, headers=headers)
                r3 = client.post("/api/v1/predict", json={"ticker": "AAPL"}, headers=headers)

            assert r1.status_code == 200
            assert r2.status_code == 200
            assert r3.status_code == 429
        finally:
            getattr(api_main, "set_rate_limit_redis_client_for_tests")(None)

    def test_metrics_endpoint_prometheus_format(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("src.config.settings.api_rate_limit_enabled", False)
        api_main.clear_rate_limiter_state()
        api_main.clear_metrics_state()

        client.get("/health")
        response = client.get("/metrics")
        assert response.status_code == 200
        assert "finsense_requests_total" in response.text
        assert "# TYPE finsense_requests_total counter" in response.text
        assert "finsense_requests_by_path_total{path=\"/health\"}" in response.text
