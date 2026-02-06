#!/bin/bash
set -e

echo "Running Alembic migrations..."
# Stamp existing schema if alembic_version table doesn't exist
# (handles first run after switching from create_all to Alembic)
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
        result = await conn.fetchval(\"\"\"
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'alembic_version'
            )
        \"\"\")
        if not result:
            print('No alembic_version table found, stamping 001...')
            exit(1)
        else:
            print('alembic_version table exists, proceeding...')
            exit(0)
    finally:
        await conn.close()
asyncio.run(check())
" || alembic stamp 001_initial_schema

alembic upgrade head
echo "Migrations complete."

echo "Starting application..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
