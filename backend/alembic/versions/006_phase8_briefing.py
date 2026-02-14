"""Phase 8 briefing: briefings table.

Revision ID: 006_phase8_briefing
Revises: 005_phase7_wellbeing
Create Date: 2026-02-14
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "006_phase8_briefing"
down_revision: Union[str, None] = "005_phase7_wellbeing"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "briefings",
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
            "briefing_date",
            sa.Date,
            nullable=False,
            server_default=sa.text("CURRENT_DATE"),
        ),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column(
            "tasks_suggested",
            postgresql.JSONB,
            nullable=False,
            server_default="[]",
        ),
        sa.Column(
            "wellbeing_snapshot",
            postgresql.JSONB,
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="generated",
        ),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
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
        comment="Daily Morning Briefings",
    )

    # One briefing per user per day + fast lookup
    op.create_index(
        "ix_briefings_user_date",
        "briefings",
        ["user_id", "briefing_date"],
        unique=True,
    )

    # Fast lookup for recent briefings
    op.create_index(
        "ix_briefings_user_created",
        "briefings",
        ["user_id", sa.text("created_at DESC")],
    )


def downgrade() -> None:
    op.drop_index("ix_briefings_user_created", table_name="briefings")
    op.drop_index("ix_briefings_user_date", table_name="briefings")
    op.drop_table("briefings")
