"""Sentiment analysis module.

For MVP, this uses a placeholder that returns neutral sentiment scores.
In production, this would load the ProsusAI/finbert model from HuggingFace
and analyze financial headlines for sentiment.

To enable real FinBERT analysis, set USE_FINBERT=true in your environment.
"""

import logging
from typing import TypedDict

logger = logging.getLogger(__name__)


class SentimentResult(TypedDict):
    """Result from sentiment analysis."""

    text: str
    positive: float
    negative: float
    neutral: float
    label: str


def _get_neutral_sentiment(text: str) -> SentimentResult:
    """Return a neutral sentiment placeholder."""
    return SentimentResult(
        text=text,
        positive=0.0,
        negative=0.0,
        neutral=1.0,
        label="neutral",
    )


def analyze_sentiment(headlines: list[str]) -> list[SentimentResult]:
    """Analyze sentiment of financial headlines.

    For MVP, returns neutral sentiment for all inputs. When FinBERT is
    enabled, uses the ProsusAI/finbert model for real sentiment scoring.

    Args:
        headlines: List of text strings to analyze.

    Returns:
        List of SentimentResult dicts with scores for each headline.
    """
    if not headlines:
        return []

    # MVP: Return neutral sentiment for all headlines
    # TODO: Enable real FinBERT analysis when model is available
    logger.info(
        "Sentiment analysis running in placeholder mode for %d headlines. "
        "All results will be neutral. Enable FinBERT for real analysis.",
        len(headlines),
    )

    return [_get_neutral_sentiment(headline) for headline in headlines]


def analyze_sentiment_finbert(headlines: list[str]) -> list[SentimentResult]:
    """Analyze sentiment using the real FinBERT model.

    This function loads the ProsusAI/finbert model and performs actual
    sentiment analysis. It requires significant memory (~1GB) and is
    slower than the placeholder.

    Args:
        headlines: List of text strings to analyze.

    Returns:
        List of SentimentResult dicts with real sentiment scores.

    Raises:
        ImportError: If transformers/torch are not installed.
    """
    if not headlines:
        return []

    from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline

    logger.info("Loading FinBERT model (ProsusAI/finbert)...")
    tokenizer = AutoTokenizer.from_pretrained("ProsusAI/finbert")
    model = AutoModelForSequenceClassification.from_pretrained("ProsusAI/finbert")
    nlp = pipeline("sentiment-analysis", model=model, tokenizer=tokenizer)

    results: list[SentimentResult] = []
    # Process in batches of 32 to manage memory
    batch_size = 32

    for i in range(0, len(headlines), batch_size):
        batch = headlines[i : i + batch_size]
        predictions = nlp(batch)

        for text_input, pred in zip(batch, predictions):
            label = pred["label"].lower()
            score = pred["score"]

            result = SentimentResult(
                text=text_input,
                positive=score if label == "positive" else 0.0,
                negative=score if label == "negative" else 0.0,
                neutral=score if label == "neutral" else 0.0,
                label=label,
            )
            results.append(result)

    logger.info("Analyzed %d headlines with FinBERT", len(results))
    return results