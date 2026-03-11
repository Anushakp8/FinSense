"""add model safety and prediction constraints

Revision ID: 003_model_safety_constraints
Revises: 002_economic_indicators
Create Date: 2026-03-10 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "003_model_safety_constraints"
down_revision: Union[str, None] = "002_economic_indicators"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enforce at most one active model in model_registry.
    op.create_index(
        "uq_model_registry_single_active",
        "model_registry",
        ["is_active"],
        unique=True,
        postgresql_where=sa.text("is_active = TRUE"),
    )

    # Hard guardrails for prediction payload integrity.
    op.create_check_constraint(
        "ck_predictions_confidence_range",
        "predictions",
        "confidence >= 0 AND confidence <= 1",
    )
    op.create_check_constraint(
        "ck_predictions_predicted_direction",
        "predictions",
        "predicted_direction IN ('UP', 'DOWN')",
    )
    op.create_check_constraint(
        "ck_predictions_actual_direction",
        "predictions",
        "actual_direction IS NULL OR actual_direction IN ('UP', 'DOWN')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_predictions_actual_direction", "predictions", type_="check")
    op.drop_constraint("ck_predictions_predicted_direction", "predictions", type_="check")
    op.drop_constraint("ck_predictions_confidence_range", "predictions", type_="check")
    op.drop_index("uq_model_registry_single_active", table_name="model_registry")
