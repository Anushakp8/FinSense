"""Shared dependencies for FastAPI route handlers.

Provides database session, Redis client, and model loader
as injectable dependencies via FastAPI's Depends system.
"""

import logging
from collections.abc import Generator
from functools import lru_cache

import redis
from fastapi import Header, HTTPException, status
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from src.config import settings

logger = logging.getLogger(__name__)

# Sync engine for API use (FastAPI runs sync handlers in threadpool)
_engine: Engine | None = None
_session_factory: sessionmaker | None = None


def get_engine() -> Engine:
    """Get or create the SQLAlchemy sync engine (singleton)."""
    global _engine
    if _engine is None:
        _engine = create_engine(
            settings.database_url_sync,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
        )
    return _engine


def get_db() -> Generator[Session, None, None]:
    """Dependency that yields a database session."""
    global _session_factory
    if _session_factory is None:
        _session_factory = sessionmaker(bind=get_engine())

    session = _session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_redis_client() -> redis.Redis:
    """Dependency that returns a Redis client."""
    try:
        client = redis.from_url(settings.redis_url, decode_responses=True)
        client.ping()
        return client
    except redis.ConnectionError:
        logger.warning("Redis unavailable, returning None-like client")
        raise


@lru_cache(maxsize=1)
def get_model_and_metadata() -> tuple[object, dict[str, object]] | None:
    """Load the active model from the registry (cached).

    Uses lru_cache so the model is only loaded once. Call
    reload_model() to clear the cache and force a reload.
    """
    from src.ml.registry import get_active_model

    engine = get_engine()
    result = get_active_model(engine)
    if result is None:
        logger.warning("No active model available")
        return None
    logger.info("Loaded model: %s v%s", result[1]["model_name"], result[1]["version"])
    return result


def reload_model() -> None:
    """Clear the model cache to force a reload on next request."""
    get_model_and_metadata.cache_clear()
    logger.info("Model cache cleared")


def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """Optionally enforce API key authentication for sensitive endpoints."""
    if not settings.api_require_key:
        return

    if not settings.api_key:
        logger.error("API key protection enabled but API_KEY is not configured")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="API authentication is misconfigured",
        )

    if x_api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )
