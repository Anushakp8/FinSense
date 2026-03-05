"""FastAPI application entry point for FinSense."""

import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.dependencies import get_engine, get_model_and_metadata
from src.api.routes import pipeline, portfolio, predict, stocks
from src.api.schemas import HealthResponse
from src.config import settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup: verify DB connection and load model
    logger.info("Starting FinSense API...")

    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(__import__("sqlalchemy").text("SELECT 1"))
        logger.info("Database connection verified")
    except Exception:
        logger.exception("Failed to connect to database")

    model_result = get_model_and_metadata()
    if model_result:
        logger.info("Active model loaded: %s", model_result[1]["version"])
    else:
        logger.warning("No active model found â€” predictions will fail until a model is trained")

    yield

    # Shutdown
    logger.info("Shutting down FinSense API")


app = FastAPI(
    title="FinSense API",
    description="Real-time financial data pipeline with ML predictions",
    version="0.5.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.api_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(predict.router)
app.include_router(portfolio.router)
app.include_router(pipeline.router)
app.include_router(stocks.router)


@app.get("/health", response_model=HealthResponse, tags=["health"])
def health_check() -> HealthResponse:
    """API health check endpoint."""
    db_status = "unknown"
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(__import__("sqlalchemy").text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "disconnected"

    return HealthResponse(
        status="ok" if db_status == "connected" else "degraded",
        database=db_status,
        timestamp=datetime.now(timezone.utc),
    )
