"""ORM model for ML model predictions."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Index, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base


class Prediction(Base):
    """ML model predictions for stock price direction.

    The `actual_direction` column is nullable â€” it gets backfilled once the
    actual outcome is known, enabling accuracy tracking over time.
    """

    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    predicted_direction: Mapped[str] = mapped_column(
        String(4), nullable=False
    )  # "UP" or "DOWN"
    confidence: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    model_version: Mapped[str] = mapped_column(String(50), nullable=False)
    actual_direction: Mapped[str | None] = mapped_column(
        String(4), nullable=True
    )  # Backfilled later
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    __table_args__ = (
        Index("ix_predictions_ticker_timestamp", "ticker", "timestamp"),
    )

    def __repr__(self) -> str:
        return (
            f"<Prediction(ticker={self.ticker!r}, "
            f"predicted={self.predicted_direction}, "
            f"confidence={self.confidence})>"
        )
