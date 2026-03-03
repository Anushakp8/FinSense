"""ORM model for raw stock price data (OHLCV)."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, DateTime, Index, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base


class RawPrice(Base):
    """Raw OHLCV stock price data.

    This table is converted to a TimescaleDB hypertable partitioned on the
    `timestamp` column for efficient time-range queries.
    """

    __tablename__ = "raw_prices"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    open: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    high: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    low: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    close: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    volume: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    __table_args__ = (
        Index("ix_raw_prices_ticker_timestamp", "ticker", "timestamp", unique=True),
    )

    def __repr__(self) -> str:
        return (
            f"<RawPrice(ticker={self.ticker!r}, timestamp={self.timestamp}, "
            f"close={self.close})>"
        )
