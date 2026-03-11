"""Tests for optional API key authentication dependency."""

import pytest
from fastapi import HTTPException

from src.api.dependencies import require_api_key


class TestRequireApiKey:

    def test_no_auth_when_disabled(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("src.api.dependencies.settings.api_require_key", False)
        require_api_key(None)

    def test_rejects_when_enabled_and_missing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("src.api.dependencies.settings.api_require_key", True)
        monkeypatch.setattr("src.api.dependencies.settings.api_key", "secret")

        with pytest.raises(HTTPException) as exc:
            require_api_key(None)

        assert exc.value.status_code == 401

    def test_rejects_when_enabled_and_invalid(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("src.api.dependencies.settings.api_require_key", True)
        monkeypatch.setattr("src.api.dependencies.settings.api_key", "secret")

        with pytest.raises(HTTPException) as exc:
            require_api_key("wrong")

        assert exc.value.status_code == 401

    def test_accepts_when_enabled_and_valid(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("src.api.dependencies.settings.api_require_key", True)
        monkeypatch.setattr("src.api.dependencies.settings.api_key", "secret")
        require_api_key("secret")

    def test_rejects_when_enabled_but_unconfigured(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("src.api.dependencies.settings.api_require_key", True)
        monkeypatch.setattr("src.api.dependencies.settings.api_key", "")

        with pytest.raises(HTTPException) as exc:
            require_api_key("anything")

        assert exc.value.status_code == 503
