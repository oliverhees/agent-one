"""Phase 2 tables: tasks, brain_entries, brain_embeddings, mentioned_items, personality.

Revision ID: 002_phase2_tables
Revises: 001_initial_schema
Create Date: 2026-02-06

This migration creates the Phase 2 Core Features tables:
- tasks: User tasks with hierarchy support
- brain_entries: Second Brain knowledge entries
- brain_embeddings: Vector embeddings for brain entries (pgvector)
- mentioned_items: Items extracted from chat messages
- personality_templates: Predefined personality presets (with seed data)
- personality_profiles: User-customizable personality profiles
"""

from typing import Sequence, Union
from uuid import uuid4

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '002_phase2_tables'
down_revision: Union[str, None] = '001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create Phase 2 tables, enums, indexes, and seed personality templates."""

    # ── Phase 2 ENUM types (via raw SQL to avoid double-creation) ────────

    op.execute("CREATE TYPE task_priority AS ENUM ('low', 'medium', 'high', 'urgent')")
    op.execute("CREATE TYPE task_status AS ENUM ('open', 'in_progress', 'done', 'cancelled')")
    op.execute("CREATE TYPE task_source AS ENUM ('manual', 'chat_extract', 'breakdown', 'recurring')")
    op.execute("CREATE TYPE brain_entry_type AS ENUM ('manual', 'chat_extract', 'url_import', 'file_import', 'voice_note')")
    op.execute("CREATE TYPE embedding_status AS ENUM ('pending', 'processing', 'completed', 'failed')")
    op.execute("CREATE TYPE mentioned_item_type AS ENUM ('task', 'appointment', 'idea', 'follow_up', 'reminder')")
    op.execute("CREATE TYPE mentioned_item_status AS ENUM ('pending', 'converted', 'dismissed', 'snoozed')")

    # Use create_type=False since we created them manually above
    task_priority = postgresql.ENUM('low', 'medium', 'high', 'urgent', name='task_priority', create_type=False)
    task_status = postgresql.ENUM('open', 'in_progress', 'done', 'cancelled', name='task_status', create_type=False)
    task_source = postgresql.ENUM('manual', 'chat_extract', 'breakdown', 'recurring', name='task_source', create_type=False)
    brain_entry_type = postgresql.ENUM('manual', 'chat_extract', 'url_import', 'file_import', 'voice_note', name='brain_entry_type', create_type=False)
    embedding_status = postgresql.ENUM('pending', 'processing', 'completed', 'failed', name='embedding_status', create_type=False)
    mentioned_item_type = postgresql.ENUM('task', 'appointment', 'idea', 'follow_up', 'reminder', name='mentioned_item_type', create_type=False)
    mentioned_item_status = postgresql.ENUM('pending', 'converted', 'dismissed', 'snoozed', name='mentioned_item_status', create_type=False)

    # ── Table: tasks ─────────────────────────────────────────────────────

    op.create_table(
        'tasks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('priority', task_priority, nullable=False, server_default='medium'),
        sa.Column('status', task_status, nullable=False, server_default='open'),
        sa.Column('due_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('xp_earned', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('parent_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_recurring', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('recurrence_rule', sa.String(length=255), nullable=True),
        sa.Column('tags', postgresql.ARRAY(sa.Text()), nullable=False, server_default='{}'),
        sa.Column('source', task_source, nullable=False, server_default='manual'),
        sa.Column('source_message_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('estimated_minutes', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE', name='fk_tasks_user_id'),
        sa.ForeignKeyConstraint(['parent_id'], ['tasks.id'], ondelete='CASCADE', name='fk_tasks_parent_id'),
        sa.ForeignKeyConstraint(['source_message_id'], ['messages.id'], ondelete='SET NULL', name='fk_tasks_source_message_id'),
        sa.CheckConstraint('parent_id != id', name='ck_tasks_no_self_parent'),
        sa.CheckConstraint("completed_at IS NULL OR status = 'done'", name='ck_tasks_completed_at_status'),
        sa.PrimaryKeyConstraint('id'),
        comment='User tasks with hierarchy support',
    )

    # Indexes for tasks
    op.create_index('ix_tasks_id', 'tasks', ['id'], unique=False)
    op.create_index('ix_tasks_user_id', 'tasks', ['user_id'], unique=False)
    op.create_index('ix_tasks_parent_id', 'tasks', ['parent_id'], unique=False)
    op.create_index('ix_tasks_user_status', 'tasks', ['user_id', 'status'], unique=False)
    op.create_index('ix_tasks_user_due_date', 'tasks', ['user_id', 'due_date'], unique=False)
    op.create_index('ix_tasks_user_status_due', 'tasks', ['user_id', 'status', 'due_date'], unique=False)
    op.create_index('ix_tasks_tags', 'tasks', ['tags'], unique=False, postgresql_using='gin')

    # ── Table: brain_entries ─────────────────────────────────────────────

    op.create_table(
        'brain_entries',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('entry_type', brain_entry_type, nullable=False, server_default='manual'),
        sa.Column('tags', postgresql.ARRAY(sa.Text()), nullable=False, server_default='{}'),
        sa.Column('source_url', sa.String(length=2000), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('embedding_status', embedding_status, nullable=False, server_default='pending'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE', name='fk_brain_entries_user_id'),
        sa.PrimaryKeyConstraint('id'),
        comment='Second Brain knowledge entries',
    )

    # Indexes for brain_entries
    op.create_index('ix_brain_entries_id', 'brain_entries', ['id'], unique=False)
    op.create_index('ix_brain_entries_user_id', 'brain_entries', ['user_id'], unique=False)
    op.create_index('ix_brain_entries_user_type', 'brain_entries', ['user_id', 'entry_type'], unique=False)
    op.create_index('ix_brain_entries_tags', 'brain_entries', ['tags'], unique=False, postgresql_using='gin')
    op.create_index(
        'ix_brain_entries_user_created',
        'brain_entries',
        [sa.text('user_id'), sa.text('created_at DESC')],
        unique=False,
    )

    # ── Table: brain_embeddings ──────────────────────────────────────────

    op.create_table(
        'brain_embeddings',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('entry_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('chunk_text', sa.Text(), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['entry_id'], ['brain_entries.id'], ondelete='CASCADE', name='fk_brain_embeddings_entry_id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE', name='fk_brain_embeddings_user_id'),
        sa.PrimaryKeyConstraint('id'),
        comment='Vector embeddings for brain entry chunks (pgvector)',
    )

    # Add vector column using raw SQL (pgvector)
    op.execute("ALTER TABLE brain_embeddings ADD COLUMN embedding vector(384) NOT NULL")

    # Indexes for brain_embeddings
    op.create_index('ix_brain_embeddings_id', 'brain_embeddings', ['id'], unique=False)
    op.create_index('ix_brain_embeddings_entry_id', 'brain_embeddings', ['entry_id'], unique=False)
    op.create_index('ix_brain_embeddings_user_id', 'brain_embeddings', ['user_id'], unique=False)

    # HNSW index for vector similarity search
    op.execute("""
        CREATE INDEX ix_brain_embeddings_vector
        ON brain_embeddings
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
    """)

    # ── Table: mentioned_items ───────────────────────────────────────────

    op.create_table(
        'mentioned_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('message_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('item_type', mentioned_item_type, nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('status', mentioned_item_status, nullable=False, server_default='pending'),
        sa.Column('extracted_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('converted_to_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('converted_to_type', sa.String(length=50), nullable=True),
        sa.Column('snoozed_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE', name='fk_mentioned_items_user_id'),
        sa.ForeignKeyConstraint(['message_id'], ['messages.id'], ondelete='CASCADE', name='fk_mentioned_items_message_id'),
        sa.PrimaryKeyConstraint('id'),
        comment='Items extracted from chat messages',
    )

    # Indexes for mentioned_items
    op.create_index('ix_mentioned_items_id', 'mentioned_items', ['id'], unique=False)
    op.create_index('ix_mentioned_items_user_id', 'mentioned_items', ['user_id'], unique=False)
    op.create_index('ix_mentioned_items_message_id', 'mentioned_items', ['message_id'], unique=False)
    op.create_index('ix_mentioned_items_user_status', 'mentioned_items', ['user_id', 'status'], unique=False)

    # ── Table: personality_templates ─────────────────────────────────────

    op.create_table(
        'personality_templates',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('traits', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('rules', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('icon', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', name='uq_personality_templates_name'),
        comment='Predefined personality templates',
    )

    op.create_index('ix_personality_templates_id', 'personality_templates', ['id'], unique=False)

    # ── Table: personality_profiles ──────────────────────────────────────

    op.create_table(
        'personality_profiles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('template_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('traits', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('rules', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('voice_style', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('custom_instructions', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE', name='fk_personality_profiles_user_id'),
        sa.ForeignKeyConstraint(['template_id'], ['personality_templates.id'], ondelete='SET NULL', name='fk_personality_profiles_template_id'),
        sa.PrimaryKeyConstraint('id'),
        comment='Customizable personality profiles for ALICE',
    )

    # Indexes for personality_profiles
    op.create_index('ix_personality_profiles_id', 'personality_profiles', ['id'], unique=False)
    op.create_index('ix_personality_profiles_user_id', 'personality_profiles', ['user_id'], unique=False)

    # Partial unique index: max 1 active profile per user
    op.execute("""
        CREATE UNIQUE INDEX ix_personality_profiles_user_active
        ON personality_profiles (user_id)
        WHERE is_active = true
    """)

    # ── Seed: personality_templates ──────────────────────────────────────

    templates_table = sa.table(
        'personality_templates',
        sa.column('id', postgresql.UUID(as_uuid=True)),
        sa.column('name', sa.String),
        sa.column('description', sa.Text),
        sa.column('traits', postgresql.JSONB),
        sa.column('rules', postgresql.JSONB),
        sa.column('is_default', sa.Boolean),
        sa.column('icon', sa.String),
    )

    op.bulk_insert(templates_table, [
        {
            'id': str(uuid4()),
            'name': 'Strenger Coach',
            'description': 'Ein disziplinierter Coach, der klare Ansagen macht und dich auf Kurs haelt. Ideal fuer alle, die einen strukturierten und direkten Begleiter wollen.',
            'traits': '{"formality": 70, "humor": 20, "strictness": 90, "empathy": 40, "verbosity": 30}',
            'rules': '[]',
            'is_default': False,
            'icon': 'shield',
        },
        {
            'id': str(uuid4()),
            'name': 'Freundlicher Begleiter',
            'description': 'Ein warmherziger und verstaendnisvoller Begleiter, der immer ein offenes Ohr hat. Perfekt fuer alle, die Ermutigung und Empathie brauchen.',
            'traits': '{"formality": 20, "humor": 70, "strictness": 20, "empathy": 90, "verbosity": 60}',
            'rules': '[]',
            'is_default': True,
            'icon': 'heart',
        },
        {
            'id': str(uuid4()),
            'name': 'Sachlicher Assistent',
            'description': 'Ein professioneller und faktenorientierter Assistent, der klar und praezise kommuniziert. Fuer alle, die Effizienz schaetzen.',
            'traits': '{"formality": 80, "humor": 10, "strictness": 50, "empathy": 50, "verbosity": 40}',
            'rules': '[]',
            'is_default': False,
            'icon': 'briefcase',
        },
        {
            'id': str(uuid4()),
            'name': 'Motivierende Cheerleaderin',
            'description': 'Eine enthusiastische und aufmunternde Persoenlichkeit, die dich anfeuert und feiert. Ideal fuer Motivationsschuebe und positive Energie.',
            'traits': '{"formality": 10, "humor": 80, "strictness": 30, "empathy": 80, "verbosity": 70}',
            'rules': '[]',
            'is_default': False,
            'icon': 'star',
        },
    ])


def downgrade() -> None:
    """Drop Phase 2 tables, indexes, and enums in reverse order."""

    # Drop partial unique index (created via raw SQL)
    op.execute("DROP INDEX IF EXISTS ix_personality_profiles_user_active")

    # Drop personality_profiles
    op.drop_index('ix_personality_profiles_user_id', table_name='personality_profiles')
    op.drop_index('ix_personality_profiles_id', table_name='personality_profiles')
    op.drop_table('personality_profiles')

    # Drop personality_templates
    op.drop_index('ix_personality_templates_id', table_name='personality_templates')
    op.drop_table('personality_templates')

    # Drop mentioned_items
    op.drop_index('ix_mentioned_items_user_status', table_name='mentioned_items')
    op.drop_index('ix_mentioned_items_message_id', table_name='mentioned_items')
    op.drop_index('ix_mentioned_items_user_id', table_name='mentioned_items')
    op.drop_index('ix_mentioned_items_id', table_name='mentioned_items')
    op.drop_table('mentioned_items')

    # Drop brain_embeddings (HNSW index dropped with table)
    op.execute("DROP INDEX IF EXISTS ix_brain_embeddings_vector")
    op.drop_index('ix_brain_embeddings_user_id', table_name='brain_embeddings')
    op.drop_index('ix_brain_embeddings_entry_id', table_name='brain_embeddings')
    op.drop_index('ix_brain_embeddings_id', table_name='brain_embeddings')
    op.drop_table('brain_embeddings')

    # Drop brain_entries
    op.execute("DROP INDEX IF EXISTS ix_brain_entries_user_created")
    op.drop_index('ix_brain_entries_tags', table_name='brain_entries')
    op.drop_index('ix_brain_entries_user_type', table_name='brain_entries')
    op.drop_index('ix_brain_entries_user_id', table_name='brain_entries')
    op.drop_index('ix_brain_entries_id', table_name='brain_entries')
    op.drop_table('brain_entries')

    # Drop tasks
    op.drop_index('ix_tasks_tags', table_name='tasks')
    op.drop_index('ix_tasks_user_status_due', table_name='tasks')
    op.drop_index('ix_tasks_user_due_date', table_name='tasks')
    op.drop_index('ix_tasks_user_status', table_name='tasks')
    op.drop_index('ix_tasks_parent_id', table_name='tasks')
    op.drop_index('ix_tasks_user_id', table_name='tasks')
    op.drop_index('ix_tasks_id', table_name='tasks')
    op.drop_table('tasks')

    # Drop Phase 2 enum types
    op.execute("DROP TYPE IF EXISTS mentioned_item_status")
    op.execute("DROP TYPE IF EXISTS mentioned_item_type")
    op.execute("DROP TYPE IF EXISTS embedding_status")
    op.execute("DROP TYPE IF EXISTS brain_entry_type")
    op.execute("DROP TYPE IF EXISTS task_source")
    op.execute("DROP TYPE IF EXISTS task_status")
    op.execute("DROP TYPE IF EXISTS task_priority")
