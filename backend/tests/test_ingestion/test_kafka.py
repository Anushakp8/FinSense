"""Tests for Kafka producer and consumer."""

import json
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from src.ingestion.kafka_consumer import StockPriceMessage, consume_and_store
from src.ingestion.kafka_producer import produce_historical_data


class TestStockPriceMessage:

    def test_valid_message(self) -> None:
        msg = StockPriceMessage(
            ticker="AAPL", timestamp="2024-01-02T00:00:00+00:00",
            open=150.0, high=155.0, low=149.0, close=154.0, volume=1000000,
        )
        assert msg.ticker == "AAPL"

    def test_empty_ticker_rejected(self) -> None:
        with pytest.raises(ValidationError):
            StockPriceMessage(
                ticker="", timestamp="2024-01-02T00:00:00+00:00",
                open=150.0, high=155.0, low=149.0, close=154.0, volume=1000000,
            )

    def test_negative_price_rejected(self) -> None:
        with pytest.raises(ValidationError):
            StockPriceMessage(
                ticker="AAPL", timestamp="2024-01-02T00:00:00+00:00",
                open=-150.0, high=155.0, low=149.0, close=154.0, volume=1000000,
            )

    def test_zero_volume_rejected(self) -> None:
        with pytest.raises(ValidationError):
            StockPriceMessage(
                ticker="AAPL", timestamp="2024-01-02T00:00:00+00:00",
                open=150.0, high=155.0, low=149.0, close=154.0, volume=0,
            )

    def test_ticker_uppercase_normalization(self) -> None:
        msg = StockPriceMessage(
            ticker="aapl", timestamp="2024-01-02T00:00:00+00:00",
            open=150.0, high=155.0, low=149.0, close=154.0, volume=1000000,
        )
        assert msg.ticker == "AAPL"


class TestKafkaProducer:

    @patch("src.ingestion.kafka_producer.Producer")
    def test_produce_reads_from_db(self, mock_producer_class: MagicMock) -> None:
        mock_producer = MagicMock()
        mock_producer_class.return_value = mock_producer

        mock_engine = MagicMock()
        mock_conn = MagicMock()

        mock_row_1 = MagicMock()
        mock_row_1.ticker = "AAPL"
        mock_row_1.timestamp = datetime(2024, 1, 2, tzinfo=timezone.utc)
        mock_row_1.open = 150.0
        mock_row_1.high = 155.0
        mock_row_1.low = 149.0
        mock_row_1.close = 154.0
        mock_row_1.volume = 1000000

        mock_row_2 = MagicMock()
        mock_row_2.ticker = "MSFT"
        mock_row_2.timestamp = datetime(2024, 1, 2, tzinfo=timezone.utc)
        mock_row_2.open = 370.0
        mock_row_2.high = 375.0
        mock_row_2.low = 369.0
        mock_row_2.close = 374.0
        mock_row_2.volume = 500000

        mock_conn.execute.return_value = [mock_row_1, mock_row_2]
        mock_engine.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_engine.connect.return_value.__exit__ = MagicMock(return_value=False)

        count = produce_historical_data(mock_engine, speed_multiplier=0, max_messages=2)
        assert count == 2
        assert mock_producer.produce.call_count == 2


class TestKafkaConsumer:

    @patch("src.ingestion.kafka_consumer.Consumer")
    def test_consume_handles_timeout(self, mock_consumer_class: MagicMock) -> None:
        mock_consumer = MagicMock()
        mock_consumer_class.return_value = mock_consumer
        mock_consumer.poll.return_value = None

        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_engine.begin.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_engine.begin.return_value.__exit__ = MagicMock(return_value=False)

        consumed, inserted, errors = consume_and_store(mock_engine, timeout_seconds=1.0)
        assert consumed == 0
        assert errors == 0
        mock_consumer.close.assert_called_once()

    @patch("src.ingestion.kafka_consumer.Consumer")
    def test_consume_validates_and_inserts(self, mock_consumer_class: MagicMock) -> None:
        mock_consumer = MagicMock()
        mock_consumer_class.return_value = mock_consumer

        valid_msg = {
            "ticker": "AAPL", "timestamp": "2024-01-02T00:00:00+00:00",
            "open": 150.0, "high": 155.0, "low": 149.0, "close": 154.0, "volume": 1000000,
        }

        mock_kafka_msg = MagicMock()
        mock_kafka_msg.error.return_value = None
        mock_kafka_msg.value.return_value = json.dumps(valid_msg).encode("utf-8")

        mock_consumer.poll.side_effect = [mock_kafka_msg, None]

        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_conn.execute.return_value = mock_result
        mock_engine.begin.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_engine.begin.return_value.__exit__ = MagicMock(return_value=False)

        consumed, inserted, errors = consume_and_store(mock_engine, timeout_seconds=1.0)
        assert consumed == 1
        assert inserted == 1
        assert errors == 0

    @patch("src.ingestion.kafka_consumer.Consumer")
    def test_consume_counts_invalid_messages(self, mock_consumer_class: MagicMock) -> None:
        mock_consumer = MagicMock()
        mock_consumer_class.return_value = mock_consumer

        mock_kafka_msg = MagicMock()
        mock_kafka_msg.error.return_value = None
        mock_kafka_msg.value.return_value = b"not json"

        mock_consumer.poll.side_effect = [mock_kafka_msg, None]

        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_engine.begin.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_engine.begin.return_value.__exit__ = MagicMock(return_value=False)

        consumed, inserted, errors = consume_and_store(mock_engine, timeout_seconds=1.0)
        assert consumed == 0
        assert errors == 1