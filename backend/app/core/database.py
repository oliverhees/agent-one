"""Database configuration and session management."""

from typing import AsyncGenerator
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.pool import NullPool

from app.core.config import settings


# Create async engine
engine = create_async_engine(
    settings.async_database_url,
    echo=settings.debug,
    future=True,
    poolclass=NullPool if settings.app_env == "test" else None,
    pool_pre_ping=True,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for FastAPI routes to get database session.

    Yields:
        AsyncSession: Database session

    Example:
        ```python
        @router.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(User))
            return result.scalars().all()
        ```
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database connection on startup.

    Schema creation is managed by Alembic migrations (run via CLI).
    This function only verifies connectivity and imports models.
    """
    # Import all models to ensure they are registered with SQLAlchemy
    from app.models import (  # noqa: F401
        User,
        Conversation,
        Message,
        RefreshToken,
        Task,
        BrainEntry,
        BrainEmbedding,
        MentionedItem,
        PersonalityProfile,
        PersonalityTemplate,
    )

    # Verify database connectivity
    async with engine.begin() as conn:
        await conn.execute(sa.text("SELECT 1"))


async def close_db() -> None:
    """Close database connection on shutdown."""
    await engine.dispose()


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Create an async session for non-request contexts (WebSocket, background tasks).

    This is similar to get_db() but returns an AsyncGenerator directly.
    Use with async context manager:

    Example:
        ```python
        async with get_async_session() as db:
            result = await db.execute(select(User))
            await db.commit()
        ```

    Yields:
        AsyncSession: Database session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
