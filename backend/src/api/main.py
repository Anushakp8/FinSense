"""FastAPI application entry point for FinSense."""

import logging
from collections import Counter
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from time import monotonic
from uuid import uuid4

import redis
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse

from src.api.dependencies import get_engine, get_model_and_metadata
from src.api.routes import pipeline, portfolio, predict, stocks
from src.api.schemas import HealthResponse
from src.config import settings

logger = logging.getLogger(__name__)
_rate_limit_store: dict[str, deque[float]] = defaultdict(deque)
_SENSITIVE_RATE_LIMIT_PATHS = ("/api/v1/predict", "/api/v1/portfolio-risk")
_rate_limit_redis_client: redis.Redis | None = None
_metrics = Counter(
    {
        "requests_total": 0,
        "rate_limited_total": 0,
        "responses_2xx_total": 0,
        "responses_4xx_total": 0,
        "responses_5xx_total": 0,
    }
)
_metrics_requests_by_path: Counter[str] = Counter()
_metrics_rate_limited_by_path: Counter[str] = Counter()


def clear_rate_limiter_state() -> None:
    """Clear in-memory rate limiter state (used by tests)."""
    _rate_limit_store.clear()


def set_rate_limit_redis_client_for_tests(client: redis.Redis | None) -> None:
    """Set rate limit Redis client for tests."""
    global _rate_limit_redis_client
    _rate_limit_redis_client = client


def clear_metrics_state() -> None:
    """Reset in-memory metrics counters (used by tests)."""
    _metrics.clear()
    _metrics.update(
        {
            "requests_total": 0,
            "rate_limited_total": 0,
            "responses_2xx_total": 0,
            "responses_4xx_total": 0,
            "responses_5xx_total": 0,
        }
    )
    _metrics_requests_by_path.clear()
    _metrics_rate_limited_by_path.clear()


def _prometheus_escape_label(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def _get_rate_limit_redis_client() -> redis.Redis | None:
    global _rate_limit_redis_client
    if not settings.api_rate_limit_use_redis:
        return None

    if _rate_limit_redis_client is not None:
        return _rate_limit_redis_client

    try:
        client = redis.from_url(settings.redis_url, decode_responses=True)
        client.ping()
        _rate_limit_redis_client = client
        return _rate_limit_redis_client
    except redis.RedisError:
        return None


def _is_rate_limited_in_memory(client_id: str, path: str, now: float) -> bool:
    window = float(settings.api_rate_limit_window_seconds)
    max_requests = settings.api_rate_limit_max_requests
    key = f"{client_id}:{path}"
    hits = _rate_limit_store[key]

    while hits and now - hits[0] > window:
        hits.popleft()

    if len(hits) >= max_requests:
        return True

    hits.append(now)
    return False


def _is_rate_limited_in_redis(client: redis.Redis, client_id: str, path: str) -> bool:
    window = settings.api_rate_limit_window_seconds
    max_requests = settings.api_rate_limit_max_requests
    redis_key = f"rate_limit:{path}:{client_id}"

    count = int(client.incr(redis_key))
    if count == 1:
        client.expire(redis_key, window)
    return count > max_requests


def _is_rate_limited(client_id: str, path: str) -> bool:
    if not settings.api_rate_limit_enabled:
        return False
    if path not in _SENSITIVE_RATE_LIMIT_PATHS:
        return False

    redis_client = _get_rate_limit_redis_client()
    if redis_client is not None:
        try:
            return _is_rate_limited_in_redis(redis_client, client_id=client_id, path=path)
        except redis.RedisError:
            logger.warning("Redis rate limiting unavailable, falling back to in-memory limiter")

    return _is_rate_limited_in_memory(client_id=client_id, path=path, now=monotonic())


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


@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    """Attach request IDs, optional rate limiting, and request logs."""
    _metrics["requests_total"] += 1
    _metrics_requests_by_path[request.url.path] += 1
    request_id = request.headers.get("x-request-id") or uuid4().hex
    client_id = request.headers.get("x-forwarded-for") or (
        request.client.host if request.client else "unknown"
    )
    start = monotonic()

    if _is_rate_limited(client_id=client_id, path=request.url.path):
        _metrics["rate_limited_total"] += 1
        _metrics_rate_limited_by_path[request.url.path] += 1
        _metrics["responses_4xx_total"] += 1
        response = JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"})
        response.headers["x-request-id"] = request_id
        return response

    response = await call_next(request)
    if 200 <= response.status_code < 300:
        _metrics["responses_2xx_total"] += 1
    elif 400 <= response.status_code < 500:
        _metrics["responses_4xx_total"] += 1
    elif response.status_code >= 500:
        _metrics["responses_5xx_total"] += 1
    response.headers["x-request-id"] = request_id

    duration_ms = (monotonic() - start) * 1000
    logger.info(
        "request_id=%s method=%s path=%s status=%s duration_ms=%.1f",
        request_id,
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response

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


@app.get("/metrics", tags=["observability"], response_class=PlainTextResponse)
def metrics() -> str:
    """Expose lightweight process metrics in Prometheus text format."""
    lines = [
        "# HELP finsense_requests_total Total HTTP requests processed",
        "# TYPE finsense_requests_total counter",
        f"finsense_requests_total {_metrics['requests_total']}",
        "# HELP finsense_rate_limited_total Requests rejected due to API rate limiting",
        "# TYPE finsense_rate_limited_total counter",
        f"finsense_rate_limited_total {_metrics['rate_limited_total']}",
        "# HELP finsense_responses_2xx_total Total HTTP 2xx responses",
        "# TYPE finsense_responses_2xx_total counter",
        f"finsense_responses_2xx_total {_metrics['responses_2xx_total']}",
        "# HELP finsense_responses_4xx_total Total HTTP 4xx responses",
        "# TYPE finsense_responses_4xx_total counter",
        f"finsense_responses_4xx_total {_metrics['responses_4xx_total']}",
        "# HELP finsense_responses_5xx_total Total HTTP 5xx responses",
        "# TYPE finsense_responses_5xx_total counter",
        f"finsense_responses_5xx_total {_metrics['responses_5xx_total']}",
        "# HELP finsense_requests_by_path_total Total HTTP requests by endpoint path",
        "# TYPE finsense_requests_by_path_total counter",
        "# HELP finsense_rate_limited_by_path_total Requests rejected due to rate limiting by endpoint path",
        "# TYPE finsense_rate_limited_by_path_total counter",
    ]

    for path, count in sorted(_metrics_requests_by_path.items()):
        safe_path = _prometheus_escape_label(path)
        lines.append(f'finsense_requests_by_path_total{{path="{safe_path}"}} {count}')

    for path, count in sorted(_metrics_rate_limited_by_path.items()):
        safe_path = _prometheus_escape_label(path)
        lines.append(f'finsense_rate_limited_by_path_total{{path="{safe_path}"}} {count}')

    return "\n".join(lines) + "\n"
