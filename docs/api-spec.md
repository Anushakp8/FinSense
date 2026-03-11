# FinSense API Specification

Base URL: `http://localhost:8000`

## Health Check

### GET /health
Returns API and database connection status.

**Response 200:**
```json
{
  "status": "ok",
  "database": "connected",
  "timestamp": "2026-03-04T00:00:00Z"
}
```

## Stock Data

### GET /api/v1/stocks
List all tracked tickers with latest prices.

**Response 200:**
```json
{
  "stocks": [
    {
      "ticker": "AAPL",
      "latest_price": 263.31,
      "change_pct": -0.17,
      "volume": 21662512,
      "timestamp": "2026-03-04T00:00:00Z"
    }
  ],
  "count": 15
}
```

### GET /api/v1/stocks/{ticker}
Detailed stock data with technical indicators.

**Response 200:**
```json
{
  "ticker": "AAPL",
  "latest_price": 263.31,
  "change_pct": -0.17,
  "previous_close": 263.76,
  "volume": 21662512,
  "timestamp": "2026-03-04T00:00:00Z",
  "technical_indicators": {
    "rsi_14": 52.48,
    "macd": 0.56,
    "macd_signal": 0.56,
    "bollinger_upper": 249.50,
    "bollinger_lower": 220.70,
    "sma_50": 233.98,
    "sma_200": 225.33
  }
}
```

### GET /api/v1/stocks/{ticker}/history
Historical OHLCV data with pagination.

**Query params:** `page` (default 1), `page_size` (default 50, max 500)

## Predictions

### POST /api/v1/predict
Generate next-day price direction prediction.

**Request:**
```json
{ "ticker": "AAPL" }
```

**Response 200:**
```json
{
  "ticker": "AAPL",
  "direction": "UP",
  "confidence": 0.5423,
  "model_version": "20260304_213400",
  "model_name": "xgboost",
  "timestamp": "2026-03-04T21:34:00Z"
}
```

## Portfolio Risk

### GET /api/v1/portfolio-risk
Calculate portfolio risk metrics.

**Query params:** `tickers` (comma-separated), `weights` (comma-separated, must sum to 1.0)

**Example:** `/api/v1/portfolio-risk?tickers=AAPL,MSFT,GOOGL&weights=0.4,0.3,0.3`

**Response 200:**
```json
{
  "var_95": -0.0198,
  "var_99": -0.0312,
  "expected_return": 0.1245,
  "max_drawdown": -0.1567,
  "annual_volatility": 0.2134,
  "individual_risks": [
    {
      "ticker": "AAPL",
      "weight": 0.4,
      "annual_volatility": 0.2456,
      "var_95": -0.0234,
      "expected_return": 0.1567
    }
  ]
}
```

## Pipeline Status

### GET /api/v1/pipeline-status
Check pipeline health and data freshness.

**Response 200:**
```json
{
  "status": "healthy",
  "last_data_update": "2026-03-04T00:00:00Z",
  "data_freshness_hours": 21.5,
  "row_counts": {
    "raw_prices": 143907,
    "technical_indicators": 136392,
    "predictions": 0,
    "model_registry": 3
  },
  "active_model": {
    "model_name": "xgboost",
    "version": "20260304_213400",
    "f1": 0.4551
  },
  "message": "All systems operational"
}
```
