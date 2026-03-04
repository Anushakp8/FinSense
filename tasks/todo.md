# FinSense - Task Tracking

## Phase 1: Project Scaffolding and Infrastructure - COMPLETE

## Phase 2: Data Ingestion Pipeline

**Goal**: Fetch historical stock data and economic indicators, store in PostgreSQL, simulate real-time streaming via Kafka.

### Tasks
- [x] 2.1 Write src/ingestion/stock_fetcher.py
- [x] 2.2 Write src/ingestion/economic_fetcher.py + ORM model + migration
- [x] 2.3 Write src/ingestion/kafka_producer.py
- [x] 2.4 Write src/ingestion/kafka_consumer.py
- [x] 2.5 Write unit tests in tests/test_ingestion/
- [ ] 2.6 Run all tests and verify they pass
- [ ] 2.7 Run stock ingestion to populate raw_prices
- [ ] 2.8 Verify data in PostgreSQL