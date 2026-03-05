"""Pydantic v2 request/response schemas for the FinSense API."""

from datetime import datetime

from pydantic import BaseModel, Field


# â”€â”€ Prediction â”€â”€

class PredictionRequest(BaseModel):
    """Request body for POST /api/v1/predict."""

    ticker: str = Field(..., min_length=1, max_length=10, examples=["AAPL"])
    date: datetime | None = Field(default=None, description="Optional target date")


class PredictionResponse(BaseModel):
    """Response for POST /api/v1/predict."""

    ticker: str
    direction: str = Field(..., pattern="^(UP|DOWN)$")
    confidence: float = Field(..., ge=0.0, le=1.0)
    model_version: str
    model_name: str
    timestamp: str


# â”€â”€ Portfolio Risk â”€â”€

class PortfolioRiskRequest(BaseModel):
    """Query params for GET /api/v1/portfolio-risk."""

    tickers: list[str] = Field(..., min_length=1, examples=[["AAPL", "MSFT", "GOOGL"]])
    weights: list[float] = Field(..., min_length=1, examples=[[0.4, 0.3, 0.3]])


class IndividualRisk(BaseModel):
    """Risk metrics for a single stock in the portfolio."""

    ticker: str
    weight: float
    annual_volatility: float
    var_95: float
    expected_return: float


class PortfolioRiskResponse(BaseModel):
    """Response for GET /api/v1/portfolio-risk."""

    var_95: float
    var_99: float
    expected_return: float
    max_drawdown: float
    annual_volatility: float
    individual_risks: list[IndividualRisk]


# â”€â”€ Pipeline Status â”€â”€

class PipelineStatusResponse(BaseModel):
    """Response for GET /api/v1/pipeline-status."""

    status: str = Field(..., pattern="^(healthy|degraded|failed)$")
    last_data_update: datetime | None
    data_freshness_hours: float | None
    row_counts: dict[str, int]
    active_model: dict[str, object] | None
    message: str


# â”€â”€ Stock Data â”€â”€

class TechnicalIndicatorsDict(BaseModel):
    """Technical indicators for a stock."""

    rsi_14: float | None = None
    macd: float | None = None
    macd_signal: float | None = None
    bollinger_upper: float | None = None
    bollinger_lower: float | None = None
    sma_50: float | None = None
    sma_200: float | None = None


class StockDataResponse(BaseModel):
    """Response for GET /api/v1/stocks/{ticker}."""

    ticker: str
    latest_price: float
    change_pct: float
    previous_close: float
    volume: int
    timestamp: datetime
    technical_indicators: TechnicalIndicatorsDict | None = None


class StockListItem(BaseModel):
    """Single item in the stocks list."""

    ticker: str
    latest_price: float
    change_pct: float
    volume: int
    timestamp: datetime


class StockListResponse(BaseModel):
    """Response for GET /api/v1/stocks."""

    stocks: list[StockListItem]
    count: int


class StockHistoryItem(BaseModel):
    """Single OHLCV row in history."""

    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int


class StockHistoryResponse(BaseModel):
    """Response for GET /api/v1/stocks/{ticker}/history."""

    ticker: str
    data: list[StockHistoryItem]
    count: int
    page: int
    page_size: int


# â”€â”€ Health â”€â”€

class HealthResponse(BaseModel):
    """Response for GET /health."""

    status: str
    database: str
    timestamp: datetime


# â”€â”€ Errors â”€â”€

class ErrorResponse(BaseModel):
    """Standard error response."""

    detail: str
    status_code: int
