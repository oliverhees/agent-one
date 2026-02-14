"""Phase 5 memory: pattern_logs table.

Revision ID: 004_phase5_memory
Revises: 003_phase3_tables
Create Date: 2026-02-14
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '004_phase5_memory'
down_revision: Union[str, None] = '003_phase3_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create pattern_logs table."""
    op.create_table(
        'pattern_logs',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text('gen_random_uuid()'),
        ),
        sa.Column(
            'user_id',
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            'conversation_id',
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column(
            'episode_id',
            sa.String(255),
            nullable=True,
            comment='Graphiti episode reference ID',
        ),
        sa.Column(
            'mood_score',
            sa.Float(),
            nullable=True,
            comment='Mood score from -1.0 (negative) to 1.0 (positive)',
        ),
        sa.Column(
            'energy_level',
            sa.Float(),
            nullable=True,
            comment='Energy level from 0.0 (low) to 1.0 (high)',
        ),
        sa.Column(
            'focus_score',
            sa.Float(),
            nullable=True,
            comment='Focus score from 0.0 (unfocused) to 1.0 (focused)',
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ['user_id'],
            ['users.id'],
            ondelete='CASCADE',
            name='fk_pattern_logs_user_id',
        ),
        sa.ForeignKeyConstraint(
            ['conversation_id'],
            ['conversations.id'],
            ondelete='SET NULL',
            name='fk_pattern_logs_conversation_id',
        ),
        comment='NLP analysis scores per conversation for trend tracking',
    )

    op.create_index(
        'ix_pattern_logs_user_date',
        'pattern_logs',
        ['user_id', sa.text('created_at DESC')],
    )
    op.create_index(
        'ix_pattern_logs_conversation',
        'pattern_logs',
        ['conversation_id'],
    )


def downgrade() -> None:
    """Drop pattern_logs table."""
    op.drop_index('ix_pattern_logs_conversation', table_name='pattern_logs')
    op.drop_index('ix_pattern_logs_user_date', table_name='pattern_logs')
    op.drop_table('pattern_logs')
