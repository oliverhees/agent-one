"""Phase 9: predicted_patterns table.

Revision ID: 007_phase9_predicted_patterns
Revises: 006_phase8_briefing
Create Date: 2026-02-14
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "007_phase9_predicted_patterns"
down_revision: Union[str, None] = "006_phase8_briefing"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "predicted_patterns",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "pattern_type",
            sa.String(30),
            nullable=False,
        ),
        sa.Column(
            "confidence",
            sa.Float,
            nullable=False,
        ),
        sa.Column(
            "predicted_for",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "time_horizon",
            sa.String(10),
            nullable=False,
        ),
        sa.Column(
            "trigger_factors",
            postgresql.JSONB,
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "graphiti_context",
            postgresql.JSONB,
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="active",
        ),
        sa.Column(
            "resolved_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        comment="ADHS behavioral pattern predictions",
    )

    # Composite index for user + status queries
    op.create_index(
        "ix_predicted_patterns_user_status",
        "predicted_patterns",
        ["user_id", "status"],
    )

    # Composite index for user + predicted_for time-based queries
    op.create_index(
        "ix_predicted_patterns_user_predicted",
        "predicted_patterns",
        ["user_id", "predicted_for"],
    )

    # Single column index for user_id (for FK constraint performance)
    op.create_index(
        "ix_predicted_patterns_user_id",
        "predicted_patterns",
        ["user_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_predicted_patterns_user_id", table_name="predicted_patterns")
    op.drop_index("ix_predicted_patterns_user_predicted", table_name="predicted_patterns")
    op.drop_index("ix_predicted_patterns_user_status", table_name="predicted_patterns")
    op.drop_table("predicted_patterns")
