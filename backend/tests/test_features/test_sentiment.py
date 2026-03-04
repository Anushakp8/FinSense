"""Tests for sentiment analysis module."""

from src.features.sentiment import analyze_sentiment


class TestAnalyzeSentiment:

    def test_empty_input(self) -> None:
        result = analyze_sentiment([])
        assert result == []

    def test_placeholder_returns_neutral(self) -> None:
        """MVP placeholder should return neutral for all inputs."""
        headlines = ["Stock market crashes", "Revenue exceeds expectations"]
        results = analyze_sentiment(headlines)
        assert len(results) == 2
        for r in results:
            assert r["label"] == "neutral"
            assert r["neutral"] == 1.0
            assert r["positive"] == 0.0
            assert r["negative"] == 0.0

    def test_preserves_input_text(self) -> None:
        headlines = ["Test headline"]
        results = analyze_sentiment(headlines)
        assert results[0]["text"] == "Test headline"

    def test_handles_many_headlines(self) -> None:
        headlines = [f"Headline {i}" for i in range(100)]
        results = analyze_sentiment(headlines)
        assert len(results) == 100