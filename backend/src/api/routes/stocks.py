"""Stock data endpoints."""

import logging

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import text

from src.api.dependencies import get_engine
from src.api.schemas import (
    StockDataResponse,
    StockHistoryItem,
    StockHistoryResponse,
    StockListItem,
    StockListResponse,
    TechnicalIndicatorsDict,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["stocks"])


@router.get("/stocks", response_model=StockListResponse)
def list_stocks() -> StockListResponse:
    """List all tracked tickers with latest prices."""
    engine = get_engine()

    query = text("""
        WITH latest AS (
            SELECT DISTINCT ON (ticker)
                ticker, timestamp, close, volume
            FROM raw_prices
            ORDER BY ticker, timestamp DESC
        ),
        prev AS (
            SELECT DISTINCT ON (ticker)
                ticker, close as prev_close
            FROM raw_prices
            WHERE timestamp < (SELECT MAX(timestamp) FROM raw_prices)
            ORDER BY ticker, timestamp DESC
        )
        SELECT l.ticker, l.close, l.volume, l.timestamp,
               COALESCE((l.close - p.prev_close) / NULLIF(p.prev_close, 0) * 100, 0) as change_pct
        FROM latest l
        LEFT JOIN prev p ON l.ticker = p.ticker
        ORDER BY l.ticker
    """)

    with engine.connect() as conn:
        result = conn.execute(query)
        rows = result.fetchall()

    stocks = [
        StockListItem(
            ticker=row[0],
            latest_price=round(float(row[1]), 2),
            volume=int(row[2]),
            timestamp=row[3],
            change_pct=round(float(row[4]), 2),
        )
        for row in rows
    ]

    return StockListResponse(stocks=stocks, count=len(stocks))


@router.get("/stocks/{ticker}", response_model=StockDataResponse)
def get_stock_detail(ticker: str) -> StockDataResponse:
    """Get detailed stock data with technical indicators."""
    ticker = ticker.upper()
    engine = get_engine()

    # Get latest two prices for change calculation
    price_query = text("""
        SELECT timestamp, open, high, low, close, volume
        FROM raw_prices
        WHERE ticker = :ticker
        ORDER BY timestamp DESC
        LIMIT 2
    """)

    with engine.connect() as conn:
        result = conn.execute(price_query, {"ticker": ticker})
        rows = result.fetchall()

    if not rows:
        raise HTTPException(status_code=404, detail=f"Ticker {ticker} not found")

    latest = rows[0]
    prev_close = float(rows[1][4]) if len(rows) > 1 else float(latest[4])
    latest_close = float(latest[4])
    change_pct = ((latest_close - prev_close) / prev_close * 100) if prev_close != 0 else 0.0

    # Get latest technical indicators
    ti_query = text("""
        SELECT rsi_14, macd, macd_signal, bollinger_upper, bollinger_lower, sma_50, sma_200
        FROM technical_indicators
        WHERE ticker = :ticker
        ORDER BY timestamp DESC
        LIMIT 1
    """)

    with engine.connect() as conn:
        ti_result = conn.execute(ti_query, {"ticker": ticker})
        ti_row = ti_result.fetchone()

    indicators = None
    if ti_row:
        indicators = TechnicalIndicatorsDict(
            rsi_14=round(float(ti_row[0]), 2) if ti_row[0] else None,
            macd=round(float(ti_row[1]), 4) if ti_row[1] else None,
            macd_signal=round(float(ti_row[2]), 4) if ti_row[2] else None,
            bollinger_upper=round(float(ti_row[3]), 2) if ti_row[3] else None,
            bollinger_lower=round(float(ti_row[4]), 2) if ti_row[4] else None,
            sma_50=round(float(ti_row[5]), 2) if ti_row[5] else None,
            sma_200=round(float(ti_row[6]), 2) if ti_row[6] else None,
        )

    return StockDataResponse(
        ticker=ticker,
        latest_price=round(latest_close, 2),
        change_pct=round(change_pct, 2),
        previous_close=round(prev_close, 2),
        volume=int(latest[5]),
        timestamp=latest[0],
        technical_indicators=indicators,
    )


@router.get("/stocks/{ticker}/history", response_model=StockHistoryResponse)
def get_stock_history(
    ticker: str,
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=50, ge=1, le=500, description="Items per page"),
) -> StockHistoryResponse:
    """Get historical OHLCV data with pagination."""
    ticker = ticker.upper()
    engine = get_engine()
    offset = (page - 1) * page_size

    query = text("""
        SELECT timestamp, open, high, low, close, volume
        FROM raw_prices
        WHERE ticker = :ticker
        ORDER BY timestamp DESC
        LIMIT :limit OFFSET :offset
    """)

    with engine.connect() as conn:
        result = conn.execute(query, {"ticker": ticker, "limit": page_size, "offset": offset})
        rows = result.fetchall()

    if not rows and page == 1:
        raise HTTPException(status_code=404, detail=f"Ticker {ticker} not found")

    data = [
        StockHistoryItem(
            timestamp=row[0],
            open=round(float(row[1]), 4),
            high=round(float(row[2]), 4),
            low=round(float(row[3]), 4),
            close=round(float(row[4]), 4),
            volume=int(row[5]),
        )
        for row in rows
    ]

    return StockHistoryResponse(
        ticker=ticker,
        data=data,
        count=len(data),
        page=page,
        page_size=page_size,
    )
