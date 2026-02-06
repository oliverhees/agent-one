"""Authentication endpoints."""

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.core.rate_limit import auth_rate_limit, standard_rate_limit
from app.schemas.auth import LoginRequest, TokenResponse, TokenRefreshRequest
from app.schemas.user import UserCreate, UserResponse
from app.services.auth import AuthService
from app.models.user import User


router = APIRouter(tags=["Auth"])


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
    description="Register a new user account and return authentication tokens.",
    dependencies=[Depends(auth_rate_limit)],
)
async def register(
    data: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Register a new user.

    - **email**: Valid email address (must be unique)
    - **password**: Password (min 8 characters)
    - **display_name**: User's display name

    Returns JWT access and refresh tokens.
    """
    auth_service = AuthService(db)
    user, access_token, refresh_token = await auth_service.register(data)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="User login",
    description="Authenticate user and return JWT tokens.",
    dependencies=[Depends(auth_rate_limit)],
)
async def login(
    data: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Authenticate user and return tokens.

    - **email**: User's email address
    - **password**: User's password

    Returns JWT access and refresh tokens.
    """
    auth_service = AuthService(db)
    user, access_token, refresh_token = await auth_service.login(
        email=data.email,
        password=data.password,
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh access token",
    description="Exchange refresh token for new access and refresh tokens (token rotation).",
)
async def refresh(
    data: TokenRefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Refresh access token using refresh token.

    Implements token rotation: old refresh token is revoked and new one is issued.

    - **refresh_token**: Valid refresh token

    Returns new JWT access and refresh tokens.
    """
    auth_service = AuthService(db)
    access_token, refresh_token = await auth_service.refresh_tokens(data.refresh_token)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="Logout user",
    description="Revoke all refresh tokens for the authenticated user.",
)
async def logout(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Logout user by revoking all refresh tokens.

    This will logout the user from all devices.

    Requires authentication via Bearer token.
    """
    auth_service = AuthService(db)
    await auth_service.logout(current_user.id)

    return {"message": "Successfully logged out"}


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current user",
    description="Get the profile of the currently authenticated user.",
    dependencies=[Depends(standard_rate_limit)],
)
async def get_me(
    current_user: User = Depends(get_current_user),
):
    """
    Get current authenticated user's profile.

    Requires authentication via Bearer token.
    """
    return UserResponse.model_validate(current_user)
