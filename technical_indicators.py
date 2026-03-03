"""ORM model for computed technical indicators."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Index, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base


class TechnicalIndicator(Base):
    """Computed technical indicators for each ticker at each timestamp.

    Indicators include RSI, MACD, Bollinger Bands, and simple moving averages.
    """

    __tablename__ = "technical_indicators"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    rsi_14: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), nullable=True)
    macd: Mapped[Decimal | None] = mapped_column(Numeric(12, 6), nullable=True)
    macd_signal: Mapped[Decimal | None] = mapped_column(Numeric(12, 6), nullable=True)
    bollinger_upper: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    bollinger_lower: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    sma_50: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    sma_200: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    __table_args__ = (
        Index(
            "ix_technical_indicators_ticker_timestamp",
            "ticker",
            "timestamp",
            unique=True,
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<TechnicalIndicator(ticker={self.ticker!r}, "
            f"timestamp={self.timestamp}, rsi_14={self.rsi_14})>"
        )
