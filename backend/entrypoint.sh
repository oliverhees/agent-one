#!/bin/bash
set -e

echo "Running Alembic migrations..."
# Check if this is an existing DB (created before Alembic was introduced)
# by looking for alembic_version AND the users table.
# - No alembic_version + has users → stamp 001 (legacy DB, tables already exist)
# - No alembic_version + no users → fresh DB, run all migrations from scratch
# - Has alembic_version → just upgrade head
python -c "
import asyncio, asyncpg, os
async def check():
    conn = await asyncpg.connect(
        host=os.environ.get('POSTGRES_HOST', 'db'),
        port=int(os.environ.get('POSTGRES_PORT', '5432')),
        database=os.environ.get('POSTGRES_DB', 'alice'),
        user=os.environ.get('POSTGRES_USER', 'alice'),
        password=os.environ.get('POSTGRES_PASSWORD', 'alice_dev_123'),
    )
    try:
        has_alembic = await conn.fetchval(\"\"\"
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'alembic_version'
            )
        \"\"\")
        if has_alembic:
            print('alembic_version table exists, proceeding with upgrade...')
            exit(0)
        has_users = await conn.fetchval(\"\"\"
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'users'
            )
        \"\"\")
        if has_users:
            print('Legacy DB detected (users exists, no alembic_version), stamping 001...')
            exit(1)
        else:
            print('Fresh DB detected, running all migrations from scratch...')
            exit(0)
    finally:
        await conn.close()
asyncio.run(check())
" || alembic stamp 001_initial_schema

alembic upgrade head
echo "Migrations complete."

echo "Starting application..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
