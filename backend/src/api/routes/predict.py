"""Prediction endpoint."""

import logging

from fastapi import APIRouter, Depends, HTTPException

from src.api.dependencies import get_engine, require_api_key
from src.api.schemas import PredictionRequest, PredictionResponse
from src.ml.predictor import predict

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["predictions"])


@router.post("/predict", response_model=PredictionResponse)
def create_prediction(
    request: PredictionRequest,
    _: None = Depends(require_api_key),
) -> PredictionResponse:
    """Generate a next-day price direction prediction for a ticker."""
    engine = get_engine()

    try:
        result = predict(engine, request.ticker, use_cache=True)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return PredictionResponse(**result)
