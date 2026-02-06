"""Pytest configuration and fixtures."""

import asyncio
from typing import AsyncGenerator, Generator
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.main import app
from app.core.config import settings
from app.core.database import get_db
from app.models.base import Base
from app.schemas.user import UserCreate
from app.services.auth import AuthService


# Override settings for testing
settings.app_env = "test"
settings.database_url = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    engine = create_async_engine(
        settings.async_database_url,
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    TestSessionLocal = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with TestSessionLocal() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def client(test_db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create a test HTTP client."""
    async def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        yield client

    app.dependency_overrides.clear()


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
    test_db: AsyncSession,
    test_user_credentials: dict[str, str],
) -> tuple[dict, str, str]:
    """
    Create a test user and return user data with tokens.

    Returns:
        tuple: (user_dict, access_token, refresh_token)
    """
    auth_service = AuthService(test_db)

    user_create = UserCreate(
        email=test_user_credentials["email"],
        password=test_user_credentials["password"],
        display_name=test_user_credentials["display_name"],
    )

    user, access_token, refresh_token = await auth_service.register(user_create)

    return {
        "id": str(user.id),
        "email": user.email,
        "display_name": user.display_name,
    }, access_token, refresh_token


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
    test_db: AsyncSession,
) -> tuple[dict, str, str]:
    """
    Create a second test user for testing access control.

    Returns:
        tuple: (user_dict, access_token, refresh_token)
    """
    auth_service = AuthService(test_db)

    user_create = UserCreate(
        email="second@example.com",
        password="SecondPassword123",
        display_name="Second User",
    )

    user, access_token, refresh_token = await auth_service.register(user_create)

    return {
        "id": str(user.id),
        "email": user.email,
        "display_name": user.display_name,
    }, access_token, refresh_token
