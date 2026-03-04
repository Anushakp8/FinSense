"""Data ingestion layer for FinSense.

Modules:
    stock_fetcher: Fetch historical OHLCV data from Yahoo Finance.
    economic_fetcher: Fetch macroeconomic indicators from FRED API.
    kafka_producer: Replay historical data as simulated real-time Kafka events.
    kafka_consumer: Consume and store data from Kafka topics.
"""