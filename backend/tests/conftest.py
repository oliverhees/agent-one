"""Pytest configuration and fixtures."""

import asyncio
import os
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

# Override database URL BEFORE importing app modules
os.environ["DATABASE_URL"] = "postgresql+asyncpg://alice:alice_dev_123@localhost:5432/alice_test"
os.environ["APP_ENV"] = "test"
os.environ["DEBUG"] = "false"

from app.models.base import Base  # noqa: E402
from app.core.rate_limit import auth_rate_limit, chat_rate_limit, standard_rate_limit  # noqa: E402


# Test database URL
TEST_DATABASE_URL = "postgresql+asyncpg://alice:alice_dev_123@localhost:5432/alice_test"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def setup_db():
    """Set up test database schema once per session."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False, pool_pre_ping=True)

    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(autouse=True)
async def clean_tables(setup_db):
    """Truncate all tables after each test for isolation."""
    yield
    # Use a fresh engine for cleanup to avoid event loop issues
    cleanup_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with cleanup_engine.begin() as conn:
        table_names = ", ".join(
            f'"{t.name}"' for t in reversed(Base.metadata.sorted_tables)
        )
        if table_names:
            await conn.execute(text(f"TRUNCATE TABLE {table_names} CASCADE"))
    await cleanup_engine.dispose()


@pytest_asyncio.fixture
async def test_db(setup_db) -> AsyncGenerator[AsyncSession, None]:
    """
    Create a separate DB session for direct service calls in tests.

    Uses a fresh engine to avoid event loop conflicts with the ASGI transport.
    """
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def client(setup_db) -> AsyncGenerator[AsyncClient, None]:
    """Create a test HTTP client that uses the test database."""
    # Import app here to ensure env vars are set
    from app.main import app

    # Reset rate limiter state for each test
    auth_rate_limit.requests.clear()
    chat_rate_limit.requests.clear()
    standard_rate_limit.requests.clear()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac


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
    """
    Create a test user via HTTP and return user data with tokens.

    Returns:
        tuple: (user_dict, access_token, refresh_token)
    """
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
    """
    Create an authenticated test HTTP client with Bearer token.

    Returns:
        AsyncClient: Client with Authorization header set
    """
    _, access_token, _ = test_user
    client.headers["Authorization"] = f"Bearer {access_token}"
    return client


@pytest_asyncio.fixture
async def second_user(
    client: AsyncClient,
) -> tuple[dict, str, str]:
    """
    Create a second test user via HTTP for testing access control.

    Returns:
        tuple: (user_dict, access_token, refresh_token)
    """
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
