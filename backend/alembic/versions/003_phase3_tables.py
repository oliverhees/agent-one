"""Phase 3 tables: user_stats, achievements, user_achievements, nudge_history, user_settings.

Revision ID: 003_phase3_tables
Revises: 002_phase2_tables
Create Date: 2026-02-06

This migration creates the Phase 3 ADHS-Modus tables:
- user_stats: Gamification stats per user (1:1 with users)
- achievements: Achievement definitions with seed data
- user_achievements: Unlocked achievements per user
- nudge_history: Nudge/reminder history
- user_settings: ADHS-specific user settings (JSONB)
"""

from typing import Sequence, Union
from uuid import uuid4

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '003_phase3_tables'
down_revision: Union[str, None] = '002_phase2_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create Phase 3 tables, enums, indexes, and seed achievements."""

    # -- Phase 3 ENUM types (via raw SQL to avoid double-creation) ----------

    op.execute("CREATE TYPE achievement_category AS ENUM ('task', 'streak', 'brain', 'social', 'special')")
    op.execute("CREATE TYPE nudge_type AS ENUM ('follow_up', 'deadline', 'streak_reminder', 'motivational')")

    # Use create_type=False since we created them manually above
    achievement_category = postgresql.ENUM(
        'task', 'streak', 'brain', 'social', 'special',
        name='achievement_category', create_type=False,
    )
    nudge_type = postgresql.ENUM(
        'follow_up', 'deadline', 'streak_reminder', 'motivational',
        name='nudge_type', create_type=False,
    )

    # -- Table: user_stats --------------------------------------------------

    op.create_table(
        'user_stats',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('total_xp', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('level', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('current_streak', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('longest_streak', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_active_date', sa.Date(), nullable=True),
        sa.Column('tasks_completed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE', name='fk_user_stats_user_id'),
        sa.UniqueConstraint('user_id', name='uq_user_stats_user_id'),
        sa.PrimaryKeyConstraint('id'),
        comment='Gamification stats per user (1:1 with users)',
    )

    op.create_index('ix_user_stats_user_id', 'user_stats', ['user_id'], unique=True)

    # -- Table: achievements ------------------------------------------------

    op.create_table(
        'achievements',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('icon', sa.String(length=100), nullable=False),
        sa.Column('category', achievement_category, nullable=False),
        sa.Column('condition_type', sa.String(length=100), nullable=False),
        sa.Column('condition_value', sa.Integer(), nullable=False),
        sa.Column('xp_reward', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.UniqueConstraint('name', name='uq_achievements_name'),
        sa.PrimaryKeyConstraint('id'),
        comment='Achievement definitions for gamification',
    )

    op.create_index('ix_achievements_category', 'achievements', ['category'], unique=False)
    op.create_index('ix_achievements_name', 'achievements', ['name'], unique=True)

    # -- Table: user_achievements -------------------------------------------

    op.create_table(
        'user_achievements',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('achievement_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('unlocked_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE', name='fk_user_achievements_user_id'),
        sa.ForeignKeyConstraint(['achievement_id'], ['achievements.id'], ondelete='CASCADE', name='fk_user_achievements_achievement_id'),
        sa.UniqueConstraint('user_id', 'achievement_id', name='uq_user_achievements_user_achievement'),
        sa.PrimaryKeyConstraint('id'),
        comment='Unlocked achievements per user',
    )

    op.create_index('ix_user_achievements_user_id', 'user_achievements', ['user_id'], unique=False)
    op.create_index('ix_user_achievements_achievement_id', 'user_achievements', ['achievement_id'], unique=False)

    # -- Table: nudge_history -----------------------------------------------

    op.create_table(
        'nudge_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('task_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('nudge_level', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('nudge_type', nudge_type, nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('delivered_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('acknowledged_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE', name='fk_nudge_history_user_id'),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ondelete='SET NULL', name='fk_nudge_history_task_id'),
        sa.PrimaryKeyConstraint('id'),
        comment='Nudge/reminder history for ADHS mode',
    )

    op.create_index('ix_nudge_history_user_id', 'nudge_history', ['user_id'], unique=False)

    # Partial index for unacknowledged nudges per user
    op.execute("""
        CREATE INDEX ix_nudge_history_user_unack
        ON nudge_history (user_id)
        WHERE acknowledged_at IS NULL
    """)

    # -- Table: user_settings -----------------------------------------------

    default_settings = (
        '{"adhs_mode": true, "nudge_intensity": "medium", "auto_breakdown": true, '
        '"gamification_enabled": true, "focus_timer_minutes": 25, '
        '"quiet_hours_start": "22:00", "quiet_hours_end": "07:00", '
        '"preferred_reminder_times": ["09:00", "14:00", "18:00"]}'
    )

    op.create_table(
        'user_settings',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('settings', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=default_settings),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE', name='fk_user_settings_user_id'),
        sa.UniqueConstraint('user_id', name='uq_user_settings_user_id'),
        sa.PrimaryKeyConstraint('id'),
        comment='ADHS-specific user settings',
    )

    op.create_index('ix_user_settings_user_id', 'user_settings', ['user_id'], unique=True)

    # -- Seed: achievements -------------------------------------------------

    achievements_table = sa.table(
        'achievements',
        sa.column('id', postgresql.UUID(as_uuid=True)),
        sa.column('name', sa.String),
        sa.column('description', sa.Text),
        sa.column('icon', sa.String),
        sa.column('category', sa.String),
        sa.column('condition_type', sa.String),
        sa.column('condition_value', sa.Integer),
        sa.column('xp_reward', sa.Integer),
        sa.column('is_active', sa.Boolean),
    )

    op.bulk_insert(achievements_table, [
        {
            'id': str(uuid4()),
            'name': 'First Steps',
            'description': 'Erledige deinen ersten Task.',
            'icon': '\U0001f3af',
            'category': 'task',
            'condition_type': 'tasks_completed',
            'condition_value': 1,
            'xp_reward': 50,
            'is_active': True,
        },
        {
            'id': str(uuid4()),
            'name': 'Getting Things Done',
            'description': 'Erledige 10 Tasks.',
            'icon': '\u2705',
            'category': 'task',
            'condition_type': 'tasks_completed',
            'condition_value': 10,
            'xp_reward': 100,
            'is_active': True,
        },
        {
            'id': str(uuid4()),
            'name': 'Century Club',
            'description': 'Erledige 100 Tasks.',
            'icon': '\U0001f4af',
            'category': 'task',
            'condition_type': 'tasks_completed',
            'condition_value': 100,
            'xp_reward': 500,
            'is_active': True,
        },
        {
            'id': str(uuid4()),
            'name': 'Week Warrior',
            'description': 'Halte eine Streak von 7 Tagen.',
            'icon': '\U0001f525',
            'category': 'streak',
            'condition_type': 'streak_days',
            'condition_value': 7,
            'xp_reward': 150,
            'is_active': True,
        },
        {
            'id': str(uuid4()),
            'name': 'Dedicated',
            'description': 'Halte eine Streak von 30 Tagen.',
            'icon': '\u2b50',
            'category': 'streak',
            'condition_type': 'streak_days',
            'condition_value': 30,
            'xp_reward': 500,
            'is_active': True,
        },
        {
            'id': str(uuid4()),
            'name': 'Brain Scholar',
            'description': 'Erstelle 10 Brain-Eintraege.',
            'icon': '\U0001f9e0',
            'category': 'brain',
            'condition_type': 'brain_entries',
            'condition_value': 10,
            'xp_reward': 100,
            'is_active': True,
        },
        {
            'id': str(uuid4()),
            'name': 'Knowledge Base',
            'description': 'Erstelle 50 Brain-Eintraege.',
            'icon': '\U0001f4da',
            'category': 'brain',
            'condition_type': 'brain_entries',
            'condition_value': 50,
            'xp_reward': 300,
            'is_active': True,
        },
        {
            'id': str(uuid4()),
            'name': 'Speed Demon',
            'description': 'Erledige einen Task in unter 5 Minuten.',
            'icon': '\u26a1',
            'category': 'special',
            'condition_type': 'task_under_5min',
            'condition_value': 1,
            'xp_reward': 75,
            'is_active': True,
        },
    ])


def downgrade() -> None:
    """Drop Phase 3 tables, indexes, and enums in reverse order."""

    # Drop partial index (created via raw SQL)
    op.execute("DROP INDEX IF EXISTS ix_nudge_history_user_unack")

    # Drop user_settings
    op.drop_index('ix_user_settings_user_id', table_name='user_settings')
    op.drop_table('user_settings')

    # Drop nudge_history
    op.drop_index('ix_nudge_history_user_id', table_name='nudge_history')
    op.drop_table('nudge_history')

    # Drop user_achievements
    op.drop_index('ix_user_achievements_achievement_id', table_name='user_achievements')
    op.drop_index('ix_user_achievements_user_id', table_name='user_achievements')
    op.drop_table('user_achievements')

    # Drop achievements
    op.drop_index('ix_achievements_name', table_name='achievements')
    op.drop_index('ix_achievements_category', table_name='achievements')
    op.drop_table('achievements')

    # Drop user_stats
    op.drop_index('ix_user_stats_user_id', table_name='user_stats')
    op.drop_table('user_stats')

    # Drop Phase 3 enum types
    op.execute("DROP TYPE IF EXISTS nudge_type")
    op.execute("DROP TYPE IF EXISTS achievement_category")
