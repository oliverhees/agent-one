"""Health check endpoints."""

from fastapi import APIRouter, status
from sqlalchemy import text
from redis.asyncio import Redis

from app import __version__
from app.core.database import engine
from app.core.config import settings


router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Health check endpoint",
    description="Check the health of the API and its services (database, redis)",
)
async def health_check():
    """
    Health check endpoint.

    Returns:
        dict: Health status of the API and services
    """
    services = {
        "db": "unknown",
        "redis": "unknown",
    }

    # Check database connection
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        services["db"] = "ok"
    except Exception as e:
        services["db"] = f"error: {str(e)}"

    # Check Redis connection
    try:
        redis = Redis.from_url(
            settings.redis_connection_url,
            decode_responses=True,
            socket_connect_timeout=2,
        )
        await redis.ping()
        await redis.close()
        services["redis"] = "ok"
    except Exception as e:
        services["redis"] = f"error: {str(e)}"

    # Determine overall status
    overall_status = "healthy" if all(
        status == "ok" for status in services.values()
    ) else "unhealthy"

    return {
        "status": overall_status,
        "version": __version__,
        "services": services,
    }
