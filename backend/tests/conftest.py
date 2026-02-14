"""Pytest configuration and fixtures."""

import asyncio
import os
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import NullPool

# Override database URL BEFORE importing app modules
os.environ["DATABASE_URL"] = "postgresql+asyncpg://alice:alice_dev_123@localhost:5434/alice_test"
os.environ["APP_ENV"] = "test"
os.environ["DEBUG"] = "false"

from app.models.base import Base  # noqa: E402
from app.core.rate_limit import auth_rate_limit, chat_rate_limit, standard_rate_limit  # noqa: E402


# Test database URL
TEST_DATABASE_URL = "postgresql+asyncpg://alice:alice_dev_123@localhost:5434/alice_test"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def setup_db():
    """Set up test database schema once per session.

    Does NOT drop tables on teardown — they persist between test runs
    for faster startup (clean_tables handles per-test isolation).
    """
    engine = create_async_engine(TEST_DATABASE_URL, echo=False, poolclass=NullPool)

    # Terminate any lingering connections from previous test runs
    async with engine.begin() as conn:
        await conn.execute(text(
            "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
            "WHERE datname = 'alice_test' AND pid <> pg_backend_pid()"
        ))

    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        # Drop and recreate to ensure clean schema
        await conn.run_sync(Base.metadata.drop_all)
        for enum_type in ["achievement_category", "nudge_type"]:
            await conn.execute(text(f"DROP TYPE IF EXISTS {enum_type} CASCADE"))
        await conn.execute(text(
            "CREATE TYPE achievement_category AS ENUM "
            "('task', 'streak', 'brain', 'social', 'special')"
        ))
        await conn.execute(text(
            "CREATE TYPE nudge_type AS ENUM "
            "('follow_up', 'deadline', 'streak_reminder', 'motivational')"
        ))
        await conn.run_sync(Base.metadata.create_all)

    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(autouse=True)
async def clean_tables(setup_db):
    """Clean all table data AFTER each test for isolation.

    Teardown order: pytest tears down in reverse setup order.
    ``client`` depends on ``clean_tables`` (via autouse), so pytest sets up
    ``clean_tables`` first, then ``client``. On teardown: ``client`` is torn
    down first (closing ASGI transport), then ``clean_tables`` runs its
    teardown (DELETE) with no competing connections.

    Uses session_replication_role=replica to skip FK constraint checks
    and a dedicated short-lived NullPool engine for the cleanup queries.
    """
    yield

    cleanup_engine = create_async_engine(
        TEST_DATABASE_URL, echo=False, poolclass=NullPool
    )
    async with cleanup_engine.begin() as conn:
        await conn.execute(text("SET session_replication_role = replica"))
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(text(f'DELETE FROM "{table.name}"'))
        await conn.execute(text("SET session_replication_role = DEFAULT"))
    await cleanup_engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def client(setup_db, clean_tables) -> AsyncGenerator[AsyncClient, None]:
    """Create a test HTTP client that uses the test database.

    Depends on ``clean_tables`` so that on teardown, this fixture is torn
    down FIRST (closing ASGI transport and releasing DB connections), and
    ``clean_tables`` teardown runs AFTER with no competing connections.
    """
    from app.main import app

    auth_rate_limit.requests.clear()
    chat_rate_limit.requests.clear()
    standard_rate_limit.requests.clear()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac


@pytest_asyncio.fixture
async def test_db(setup_db) -> AsyncGenerator[AsyncSession, None]:
    """Create a separate DB session for direct service calls in tests."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False, poolclass=NullPool)
    session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_factory() as session:
        yield session
    await engine.dispose()


@pytest_asyncio.fixture
async def test_user_credentials() -> dict[str, str]:
    """Provide test user credentials."""
    return {
        "email": "test@example.com",
        "password": "TestPassword123",
        "display_name": "Test User",
    }


@pytest_asyncio.fixture
async def test_user(
    client: AsyncClient,
    test_user_credentials: dict[str, str],
) -> tuple[dict, str, str]:
    """Create a test user via HTTP and return user data with tokens."""
    response = await client.post(
        "/api/v1/auth/register",
        json=test_user_credentials,
    )
    assert response.status_code == 201, f"Failed to create test user: {response.text}"
    tokens = response.json()

    me_response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert me_response.status_code == 200
    user_data = me_response.json()

    return {
        "id": user_data["id"],
        "email": user_data["email"],
        "display_name": user_data["display_name"],
    }, tokens["access_token"], tokens["refresh_token"]


@pytest_asyncio.fixture
async def authenticated_client(
    client: AsyncClient,
    test_user: tuple[dict, str, str],
) -> AsyncClient:
    """Create an authenticated test HTTP client with Bearer token."""
    _, access_token, _ = test_user
    client.headers["Authorization"] = f"Bearer {access_token}"
    return client


@pytest_asyncio.fixture
async def second_user(
    client: AsyncClient,
) -> tuple[dict, str, str]:
    """Create a second test user via HTTP for testing access control."""
    creds = {
        "email": "second@example.com",
        "password": "SecondPassword123",
        "display_name": "Second User",
    }

    response = await client.post("/api/v1/auth/register", json=creds)
    assert response.status_code == 201
    tokens = response.json()

    me_response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert me_response.status_code == 200
    user_data = me_response.json()

    return {
        "id": user_data["id"],
        "email": user_data["email"],
        "display_name": user_data["display_name"],
    }, tokens["access_token"], tokens["refresh_token"]
