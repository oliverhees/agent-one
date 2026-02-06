"""FastAPI dependencies for authentication and database access."""

from typing import AsyncGenerator
from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import verify_token
from app.core.exceptions import UnauthorizedError, AccountDisabledError
from app.models.user import User


# HTTP Bearer token security
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    FastAPI dependency to get authenticated user from JWT token.

    Args:
        credentials: HTTP Bearer credentials from Authorization header
        db: Database session

    Returns:
        User: Authenticated user object

    Raises:
        UnauthorizedError: If token is invalid or user not found
        AccountDisabledError: If user account is disabled

    Example:
        ```python
        @router.get("/me")
        async def get_me(current_user: User = Depends(get_current_user)):
            return {"user_id": current_user.id}
        ```
    """
    token = credentials.credentials

    # Verify and decode token
    try:
        payload = verify_token(token, token_type="access")
    except Exception as e:
        raise UnauthorizedError(detail=str(e))

    # Extract user ID from token
    user_id_str = payload.get("sub")
    if user_id_str is None:
        raise UnauthorizedError(detail="Token payload missing user ID")

    try:
        user_id = UUID(user_id_str)
    except ValueError:
        raise UnauthorizedError(detail="Invalid user ID in token")

    # Fetch user from database
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise UnauthorizedError(detail="User not found")

    if not user.is_active:
        raise AccountDisabledError()

    return user
