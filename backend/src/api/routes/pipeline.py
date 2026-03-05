"""Pipeline status and health monitoring endpoint."""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter
from sqlalchemy import text

from src.api.dependencies import get_engine, get_model_and_metadata
from src.api.schemas import PipelineStatusResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["pipeline"])


@router.get("/pipeline-status", response_model=PipelineStatusResponse)
def get_pipeline_status() -> PipelineStatusResponse:
    """Check pipeline health: data freshness, row counts, model status."""
    engine = get_engine()

    # Row counts
    row_counts: dict[str, int] = {}
    for table in ["raw_prices", "technical_indicators", "predictions", "model_registry"]:
        with engine.connect() as conn:
            result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))  # noqa: S608
            row_counts[table] = result.scalar() or 0

    # Data freshness
    with engine.connect() as conn:
        result = conn.execute(text("SELECT MAX(timestamp) FROM raw_prices"))
        last_update = result.scalar()

    freshness_hours = None
    if last_update:
        if last_update.tzinfo is None:
            last_update = last_update.replace(tzinfo=timezone.utc)
        freshness_hours = round(
            (datetime.now(timezone.utc) - last_update).total_seconds() / 3600, 1
        )

    # Active model
    model_result = get_model_and_metadata()
    active_model = None
    if model_result:
        _, metadata = model_result
        active_model = {
            "model_name": metadata["model_name"],
            "version": metadata["version"],
            "f1": metadata["f1"],
        }

    # Determine overall status
    status = "healthy"
    messages = []

    if freshness_hours is not None and freshness_hours > 48:
        status = "degraded"
        messages.append(f"Data is {freshness_hours:.0f}h stale")

    if row_counts.get("raw_prices", 0) == 0:
        status = "failed"
        messages.append("No price data in database")

    if active_model is None:
        if status != "failed":
            status = "degraded"
        messages.append("No active model")

    message = "; ".join(messages) if messages else "All systems operational"

    return PipelineStatusResponse(
        status=status,
        last_data_update=last_update,
        data_freshness_hours=freshness_hours,
        row_counts=row_counts,
        active_model=active_model,
        message=message,
    )
