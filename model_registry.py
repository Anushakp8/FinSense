"""ORM model for ML model versioning and registry."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, Index, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base


class ModelRegistry(Base):
    """Registry of trained ML models with performance metrics.

    Only one model should have `is_active=True` at any given time.
    The active model is used for serving predictions.
    """

    __tablename__ = "model_registry"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    version: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    accuracy: Mapped[Decimal] = mapped_column(Numeric(6, 4), nullable=False)
    precision_score: Mapped[Decimal] = mapped_column(Numeric(6, 4), nullable=False)
    recall: Mapped[Decimal] = mapped_column(Numeric(6, 4), nullable=False)
    f1: Mapped[Decimal] = mapped_column(Numeric(6, 4), nullable=False)
    trained_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    model_path: Mapped[str] = mapped_column(String(500), nullable=False)

    __table_args__ = (
        Index("ix_model_registry_is_active", "is_active"),
    )

    def __repr__(self) -> str:
        return (
            f"<ModelRegistry(name={self.model_name!r}, version={self.version!r}, "
            f"f1={self.f1}, active={self.is_active})>"
        )
