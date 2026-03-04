"""Kafka producer for simulated real-time stock price streaming."""

import json
import logging
import time
from datetime import datetime, timezone

from confluent_kafka import Producer
from sqlalchemy import text
from sqlalchemy.engine import Engine

from src.config import settings

logger = logging.getLogger(__name__)

TOPIC_NAME = "stock-prices"


def _delivery_callback(err: object, msg: object) -> None:
    """Callback invoked per message to report delivery status."""
    if err is not None:
        logger.error("Message delivery failed: %s", err)


def create_producer() -> Producer:
    """Create and return a configured Kafka producer."""
    conf = {
        "bootstrap.servers": settings.kafka_bootstrap_servers,
        "client.id": "finsense-stock-producer",
        "acks": "all",
        "retries": 3,
        "linger.ms": 10,
        "batch.num.messages": 100,
    }
    return Producer(conf)


def produce_historical_data(
    engine: Engine,
    speed_multiplier: float = 1.0,
    max_messages: int | None = None,
    ticker_filter: str | None = None,
) -> int:
    """Replay historical price data as Kafka messages."""
    producer = create_producer()

    query = "SELECT ticker, timestamp, open, high, low, close, volume FROM raw_prices"
    params: dict[str, object] = {}

    if ticker_filter:
        query += " WHERE ticker = :ticker"
        params["ticker"] = ticker_filter

    query += " ORDER BY timestamp ASC, ticker ASC"

    if max_messages:
        query += " LIMIT :limit"
        params["limit"] = max_messages

    logger.info(
        "Starting Kafka producer (speed=%.1fx, max=%s, ticker=%s)",
        speed_multiplier, max_messages or "unlimited", ticker_filter or "all",
    )

    count = 0
    prev_timestamp: datetime | None = None

    with engine.connect() as conn:
        result = conn.execute(text(query), params)

        for row in result:
            message = {
                "ticker": row.ticker,
                "timestamp": row.timestamp.isoformat(),
                "open": float(row.open),
                "high": float(row.high),
                "low": float(row.low),
                "close": float(row.close),
                "volume": int(row.volume),
                "produced_at": datetime.now(timezone.utc).isoformat(),
            }

            if speed_multiplier > 0 and prev_timestamp is not None:
                time_diff = (row.timestamp - prev_timestamp).total_seconds()
                if time_diff > 0:
                    sleep_time = min(time_diff / speed_multiplier, 5.0)
                    time.sleep(sleep_time)

            producer.produce(
                topic=TOPIC_NAME,
                key=row.ticker.encode("utf-8"),
                value=json.dumps(message).encode("utf-8"),
                callback=_delivery_callback,
            )

            count += 1
            prev_timestamp = row.timestamp

            if count % 100 == 0:
                producer.flush(timeout=5)
                logger.info("Produced %d messages so far...", count)

    producer.flush(timeout=30)
    logger.info("Finished producing %d messages to topic '%s'", count, TOPIC_NAME)
    return count


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    from sqlalchemy import create_engine

    sync_engine = create_engine(settings.database_url_sync)
    produced = produce_historical_data(sync_engine, speed_multiplier=0, max_messages=100)
    print(f"\nDone! Produced {produced} messages.")