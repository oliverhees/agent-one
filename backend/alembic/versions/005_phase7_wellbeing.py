"""Phase 7 wellbeing: wellbeing_scores and interventions tables.

Revision ID: 005_phase7_wellbeing
Revises: 004_phase5_memory
Create Date: 2026-02-14
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '005_phase7_wellbeing'
down_revision: Union[str, None] = '004_phase5_memory'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create wellbeing_scores and interventions tables."""

    # Create wellbeing_scores table
    op.create_table(
        'wellbeing_scores',
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
            'score',
            sa.Float(),
            nullable=False,
            comment='Overall wellbeing score from 0.0 to 1.0',
        ),
        sa.Column(
            'zone',
            sa.String(10),
            nullable=False,
            comment='Wellbeing zone: green, yellow, orange, red',
        ),
        sa.Column(
            'components',
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
            comment='Detailed component scores (mood, energy, focus, etc.)',
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ['user_id'],
            ['users.id'],
            ondelete='CASCADE',
            name='fk_wellbeing_scores_user_id',
        ),
        comment='Daily wellbeing scores calculated from pattern analysis',
    )

    op.create_index(
        'ix_wellbeing_scores_user_date',
        'wellbeing_scores',
        ['user_id', sa.text('created_at DESC')],
    )

    # Create interventions table
    op.create_table(
        'interventions',
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
            'type',
            sa.String(30),
            nullable=False,
            comment='Intervention type: reminder, suggestion, warning, alert',
        ),
        sa.Column(
            'trigger_pattern',
            sa.String(100),
            nullable=False,
            comment='Pattern that triggered this intervention',
        ),
        sa.Column(
            'message',
            sa.Text(),
            nullable=False,
            comment='Intervention message text',
        ),
        sa.Column(
            'status',
            sa.String(20),
            nullable=False,
            server_default=sa.text("'pending'"),
            comment='Status: pending, sent, acknowledged, dismissed',
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ['user_id'],
            ['users.id'],
            ondelete='CASCADE',
            name='fk_interventions_user_id',
        ),
        comment='Proactive interventions triggered by pattern analysis',
    )

    op.create_index(
        'ix_interventions_user_status',
        'interventions',
        ['user_id', 'status'],
    )
    op.create_index(
        'ix_interventions_user_date',
        'interventions',
        ['user_id', sa.text('created_at DESC')],
    )


def downgrade() -> None:
    """Drop interventions and wellbeing_scores tables."""

    # Drop interventions table (reverse order)
    op.drop_index('ix_interventions_user_date', table_name='interventions')
    op.drop_index('ix_interventions_user_status', table_name='interventions')
    op.drop_table('interventions')

    # Drop wellbeing_scores table
    op.drop_index('ix_wellbeing_scores_user_date', table_name='wellbeing_scores')
    op.drop_table('wellbeing_scores')
