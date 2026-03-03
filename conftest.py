"""Shared test fixtures for the FinSense test suite."""

import pytest


@pytest.fixture
def sample_tickers() -> list[str]:
    """Return the list of tracked tickers."""
    return [
        "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA",
        "META", "TSLA", "JPM", "V", "JNJ",
        "WMT", "PG", "DIS", "NFLX", "AMD",
    ]
