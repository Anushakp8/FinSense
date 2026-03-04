"""Kafka consumer for real-time stock price ingestion."""

import json
import logging
from datetime import datetime, timezone

from confluent_kafka import Consumer, KafkaError, KafkaException
from pydantic import BaseModel, field_validator
from sqlalchemy import text
from sqlalchemy.engine import Engine

from src.config import settings

logger = logging.getLogger(__name__)

TOPIC_NAME = "stock-prices"
CONSUMER_GROUP = "finsense-price-consumer"


class StockPriceMessage(BaseModel):
    """Schema for validating incoming Kafka messages."""

    ticker: str
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: int

    @field_validator("ticker")
    @classmethod
    def ticker_must_be_nonempty(cls, v: str) -> str:
        if not v or not v.strip():
            msg = "ticker must not be empty"
            raise ValueError(msg)
        return v.strip().upper()

    @field_validator("open", "high", "low", "close")
    @classmethod
    def prices_must_be_positive(cls, v: float) -> float:
        if v <= 0:
            msg = "price must be positive"
            raise ValueError(msg)
        return round(v, 4)

    @field_validator("volume")
    @classmethod
    def volume_must_be_positive(cls, v: int) -> int:
        if v <= 0:
            msg = "volume must be positive"
            raise ValueError(msg)
        return v


def create_consumer() -> Consumer:
    """Create and return a configured Kafka consumer."""
    conf = {
        "bootstrap.servers": settings.kafka_bootstrap_servers,
        "group.id": CONSUMER_GROUP,
        "auto.offset.reset": "earliest",
        "enable.auto.commit": True,
        "auto.commit.interval.ms": 5000,
    }
    return Consumer(conf)


def _insert_message(conn: object, msg: StockPriceMessage) -> bool:
    """Insert a single validated message into raw_prices."""
    insert_sql = text("""
        INSERT INTO raw_prices (ticker, timestamp, open, high, low, close, volume)
        VALUES (:ticker, :timestamp, :open, :high, :low, :close, :volume)
        ON CONFLICT (ticker, timestamp) DO NOTHING
    """)

    timestamp = datetime.fromisoformat(msg.timestamp)
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)

    result = conn.execute(insert_sql, {
        "ticker": msg.ticker,
        "timestamp": timestamp,
        "open": msg.open,
        "high": msg.high,
        "low": msg.low,
        "close": msg.close,
        "volume": msg.volume,
    })
    return result.rowcount > 0


def consume_and_store(
    engine: Engine,
    max_messages: int | None = None,
    timeout_seconds: float = 30.0,
) -> tuple[int, int, int]:
    """Consume messages from Kafka and store in the database."""
    consumer = create_consumer()
    consumer.subscribe([TOPIC_NAME])

    consumed = 0
    inserted = 0
    errors = 0

    logger.info(
        "Consumer started (max_messages=%s, timeout=%.0fs)",
        max_messages or "unlimited", timeout_seconds,
    )

    try:
        with engine.begin() as conn:
            while True:
                if max_messages and consumed >= max_messages:
                    logger.info("Reached max_messages limit (%d)", max_messages)
                    break

                msg = consumer.poll(timeout=timeout_seconds)

                if msg is None:
                    logger.info("No message received within timeout, stopping")
                    break

                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        continue
                    raise KafkaException(msg.error())

                try:
                    raw_data = json.loads(msg.value().decode("utf-8"))
                    validated = StockPriceMessage(**raw_data)

                    was_inserted = _insert_message(conn, validated)
                    consumed += 1
                    if was_inserted:
                        inserted += 1

                    if consumed % 100 == 0:
                        logger.info(
                            "Progress: consumed=%d, inserted=%d, errors=%d",
                            consumed, inserted, errors,
                        )

                except (json.JSONDecodeError, ValueError) as e:
                    errors += 1
                    logger.warning("Invalid message: %s", e)
                    continue

    except KeyboardInterrupt:
        logger.info("Consumer interrupted by user")
    finally:
        consumer.close()

    logger.info(
        "Consumer finished: consumed=%d, inserted=%d, errors=%d",
        consumed, inserted, errors,
    )
    return consumed, inserted, errors


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    from sqlalchemy import create_engine

    sync_engine = create_engine(settings.database_url_sync)
    consumed, inserted, errors = consume_and_store(sync_engine, max_messages=100, timeout_seconds=10.0)
    print(f"\nDone! Consumed={consumed}, Inserted={inserted}, Errors={errors}")