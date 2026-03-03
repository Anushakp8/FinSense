"""initial schema with all four tables

Revision ID: 001_initial
Revises:
Create Date: 2025-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # â”€â”€ Ensure TimescaleDB extension is enabled â”€â”€
    op.execute("CREATE EXTENSION IF NOT EXISTS timescaledb")

    # â”€â”€ raw_prices â”€â”€
    op.create_table(
        "raw_prices",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("ticker", sa.String(length=10), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("open", sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column("high", sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column("low", sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column("close", sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column("volume", sa.BigInteger(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_raw_prices")),
    )
    op.create_index("ix_raw_prices_ticker", "raw_prices", ["ticker"])
    op.create_index(
        "ix_raw_prices_ticker_timestamp",
        "raw_prices",
        ["ticker", "timestamp"],
        unique=True,
    )

    # Convert raw_prices to a TimescaleDB hypertable
    op.execute(
        "SELECT create_hypertable('raw_prices', 'timestamp', "
        "migrate_data => true, if_not_exists => true)"
    )

    # â”€â”€ technical_indicators â”€â”€
    op.create_table(
        "technical_indicators",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("ticker", sa.String(length=10), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("rsi_14", sa.Numeric(precision=8, scale=4), nullable=True),
        sa.Column("macd", sa.Numeric(precision=12, scale=6), nullable=True),
        sa.Column("macd_signal", sa.Numeric(precision=12, scale=6), nullable=True),
        sa.Column("bollinger_upper", sa.Numeric(precision=12, scale=4), nullable=True),
        sa.Column("bollinger_lower", sa.Numeric(precision=12, scale=4), nullable=True),
        sa.Column("sma_50", sa.Numeric(precision=12, scale=4), nullable=True),
        sa.Column("sma_200", sa.Numeric(precision=12, scale=4), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_technical_indicators")),
    )
    op.create_index("ix_technical_indicators_ticker", "technical_indicators", ["ticker"])
    op.create_index(
        "ix_technical_indicators_ticker_timestamp",
        "technical_indicators",
        ["ticker", "timestamp"],
        unique=True,
    )

    # â”€â”€ predictions â”€â”€
    op.create_table(
        "predictions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("ticker", sa.String(length=10), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("predicted_direction", sa.String(length=4), nullable=False),
        sa.Column("confidence", sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column("model_version", sa.String(length=50), nullable=False),
        sa.Column("actual_direction", sa.String(length=4), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_predictions")),
    )
    op.create_index("ix_predictions_ticker", "predictions", ["ticker"])
    op.create_index(
        "ix_predictions_ticker_timestamp",
        "predictions",
        ["ticker", "timestamp"],
    )

    # â”€â”€ model_registry â”€â”€
    op.create_table(
        "model_registry",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("model_name", sa.String(length=100), nullable=False),
        sa.Column("version", sa.String(length=50), nullable=False),
        sa.Column("accuracy", sa.Numeric(precision=6, scale=4), nullable=False),
        sa.Column("precision_score", sa.Numeric(precision=6, scale=4), nullable=False),
        sa.Column("recall", sa.Numeric(precision=6, scale=4), nullable=False),
        sa.Column("f1", sa.Numeric(precision=6, scale=4), nullable=False),
        sa.Column("trained_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("model_path", sa.String(length=500), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_model_registry")),
        sa.UniqueConstraint("version", name=op.f("uq_model_registry_version")),
    )
    op.create_index("ix_model_registry_is_active", "model_registry", ["is_active"])


def downgrade() -> None:
    op.drop_table("model_registry")
    op.drop_table("predictions")
    op.drop_table("technical_indicators")
    op.drop_table("raw_prices")
