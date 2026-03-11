"""Portfolio risk analysis endpoint."""

import logging

import numpy as np
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text

from src.api.dependencies import get_engine, require_api_key
from src.api.schemas import IndividualRisk, PortfolioRiskResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["portfolio"])


def _get_returns(engine, ticker: str, days: int = 252) -> np.ndarray:
    """Fetch daily returns for a ticker."""
    query = text("""
        SELECT close FROM raw_prices
        WHERE ticker = :ticker
        ORDER BY timestamp DESC
        LIMIT :limit
    """)
    with engine.connect() as conn:
        result = conn.execute(query, {"ticker": ticker, "limit": days + 1})
        prices = [float(row[0]) for row in result]

    if len(prices) < 2:
        return np.array([])

    prices = np.array(prices[::-1])  # Reverse to chronological order
    returns = np.diff(prices) / prices[:-1]
    return returns


@router.get("/portfolio-risk", response_model=PortfolioRiskResponse)
def get_portfolio_risk(
    tickers: str = Query(..., description="Comma-separated ticker list", examples=["AAPL,MSFT,GOOGL"]),
    weights: str = Query(..., description="Comma-separated weights", examples=["0.4,0.3,0.3"]),
    _: None = Depends(require_api_key),
) -> PortfolioRiskResponse:
    """Calculate portfolio risk metrics using historical simulation."""
    ticker_list = [t.strip().upper() for t in tickers.split(",")]
    try:
        weight_list = [float(w.strip()) for w in weights.split(",")]
    except ValueError:
        raise HTTPException(status_code=400, detail="Weights must be numeric values")

    if len(ticker_list) != len(weight_list):
        raise HTTPException(
            status_code=400,
            detail=f"Number of tickers ({len(ticker_list)}) must match weights ({len(weight_list)})",
        )

    weight_sum = sum(weight_list)
    if abs(weight_sum - 1.0) > 0.01:
        raise HTTPException(
            status_code=400,
            detail=f"Weights must sum to 1.0 (got {weight_sum:.4f})",
        )

    engine = get_engine()
    all_returns: dict[str, np.ndarray] = {}
    individual_risks: list[IndividualRisk] = []

    for ticker, weight in zip(ticker_list, weight_list):
        returns = _get_returns(engine, ticker)
        if len(returns) == 0:
            raise HTTPException(status_code=404, detail=f"No price data for ticker {ticker}")
        all_returns[ticker] = returns

        annual_vol = float(np.std(returns) * np.sqrt(252))
        var_95 = float(np.percentile(returns, 5))
        expected_return = float(np.mean(returns) * 252)

        individual_risks.append(IndividualRisk(
            ticker=ticker,
            weight=weight,
            annual_volatility=round(annual_vol, 4),
            var_95=round(var_95, 6),
            expected_return=round(expected_return, 4),
        ))

    # Portfolio-level metrics using historical simulation
    min_len = min(len(r) for r in all_returns.values())
    weights_arr = np.array(weight_list)

    # Align all return series to same length
    return_matrix = np.column_stack([
        all_returns[ticker][:min_len] for ticker in ticker_list
    ])

    portfolio_returns = return_matrix @ weights_arr

    var_95 = float(np.percentile(portfolio_returns, 5))
    var_99 = float(np.percentile(portfolio_returns, 1))
    expected_return = float(np.mean(portfolio_returns) * 252)
    annual_vol = float(np.std(portfolio_returns) * np.sqrt(252))

    cumulative = np.cumprod(1 + portfolio_returns)
    running_max = np.maximum.accumulate(cumulative)
    drawdowns = (cumulative - running_max) / running_max
    max_drawdown = float(np.min(drawdowns))

    return PortfolioRiskResponse(
        var_95=round(var_95, 6),
        var_99=round(var_99, 6),
        expected_return=round(expected_return, 4),
        max_drawdown=round(max_drawdown, 4),
        annual_volatility=round(annual_vol, 4),
        individual_risks=individual_risks,
    )
