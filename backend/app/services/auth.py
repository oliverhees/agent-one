"""Authentication service for user registration, login, and token management."""

from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_token,
)
from app.core.exceptions import (
    AuthenticationError,
    EmailAlreadyExistsError,
    InvalidTokenError,
    AccountDisabledError,
)
from app.models.user import User
from app.models.refresh_token import RefreshToken
from app.schemas.user import UserCreate


class AuthService:
    """Service for authentication operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize auth service.

        Args:
            db: Database session
        """
        self.db = db

    async def register(self, data: UserCreate) -> tuple[User, str, str]:
        """
        Register a new user.

        Args:
            data: User registration data (email, password, display_name)

        Returns:
            tuple: (user, access_token, refresh_token)

        Raises:
            EmailAlreadyExistsError: If email is already registered
        """
        # Check if email already exists
        result = await self.db.execute(
            select(User).where(User.email == data.email)
        )
        existing_user = result.scalar_one_or_none()

        if existing_user:
            raise EmailAlreadyExistsError(email=data.email)

        # Hash password
        password_hash = hash_password(data.password)

        # Create user
        user = User(
            email=data.email,
            password_hash=password_hash,
            display_name=data.display_name,
            is_active=True,
        )

        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)

        # Generate tokens
        access_token = create_access_token(data={"sub": str(user.id)})
        refresh_token_str = create_refresh_token(data={"sub": str(user.id)})

        # Store refresh token in database
        expires_at = datetime.utcnow() + timedelta(days=settings.jwt_refresh_token_expire_days)
        refresh_token = RefreshToken(
            user_id=user.id,
            token=refresh_token_str,
            expires_at=expires_at,
            is_revoked=False,
        )

        self.db.add(refresh_token)
        await self.db.commit()
        await self.db.refresh(user)

        return user, access_token, refresh_token_str

    async def login(self, email: str, password: str) -> tuple[User, str, str]:
        """
        Authenticate user and create tokens.

        Args:
            email: User email
            password: User password

        Returns:
            tuple: (user, access_token, refresh_token)

        Raises:
            AuthenticationError: If credentials are invalid
            AccountDisabledError: If account is disabled
        """
        # Find user by email
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()

        if not user:
            raise AuthenticationError()

        # Verify password
        if not verify_password(password, user.password_hash):
            raise AuthenticationError()

        # Check if account is active
        if not user.is_active:
            raise AccountDisabledError()

        # Generate tokens
        access_token = create_access_token(data={"sub": str(user.id)})
        refresh_token_str = create_refresh_token(data={"sub": str(user.id)})

        # Store refresh token in database
        expires_at = datetime.utcnow() + timedelta(days=settings.jwt_refresh_token_expire_days)
        refresh_token = RefreshToken(
            user_id=user.id,
            token=refresh_token_str,
            expires_at=expires_at,
            is_revoked=False,
        )

        self.db.add(refresh_token)
        await self.db.commit()

        return user, access_token, refresh_token_str

    async def refresh_tokens(self, refresh_token_str: str) -> tuple[str, str]:
        """
        Refresh access token using refresh token (with token rotation).

        Args:
            refresh_token_str: Refresh token string

        Returns:
            tuple: (new_access_token, new_refresh_token)

        Raises:
            InvalidTokenError: If refresh token is invalid, expired, or revoked
        """
        # Verify refresh token
        try:
            payload = verify_token(refresh_token_str, token_type="refresh")
        except Exception:
            raise InvalidTokenError()

        user_id_str = payload.get("sub")
        if not user_id_str:
            raise InvalidTokenError()

        try:
            user_id = UUID(user_id_str)
        except ValueError:
            raise InvalidTokenError()

        # Check if refresh token exists in database and is not revoked
        result = await self.db.execute(
            select(RefreshToken).where(
                RefreshToken.token == refresh_token_str,
                RefreshToken.is_revoked == False,
            )
        )
        db_token = result.scalar_one_or_none()

        if not db_token:
            raise InvalidTokenError(detail="Refresh token not found or already used")

        # Check if token is expired
        if db_token.expires_at < datetime.utcnow():
            raise InvalidTokenError(detail="Refresh token has expired")

        # Verify user exists and is active
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()

        if not user or not user.is_active:
            raise InvalidTokenError(detail="User not found or account disabled")

        # Revoke old refresh token (token rotation)
        db_token.is_revoked = True

        # Generate new tokens
        new_access_token = create_access_token(data={"sub": str(user.id)})
        new_refresh_token_str = create_refresh_token(data={"sub": str(user.id)})

        # Store new refresh token in database
        expires_at = datetime.utcnow() + timedelta(days=settings.jwt_refresh_token_expire_days)
        new_refresh_token = RefreshToken(
            user_id=user.id,
            token=new_refresh_token_str,
            expires_at=expires_at,
            is_revoked=False,
        )

        self.db.add(new_refresh_token)
        await self.db.commit()

        return new_access_token, new_refresh_token_str

    async def logout(self, user_id: UUID) -> None:
        """
        Revoke all refresh tokens for a user (logout from all devices).

        Args:
            user_id: User ID to logout

        Note:
            In a production system with Redis, we would also add the access token
            to a blacklist. For now, we only revoke refresh tokens.
        """
        # Revoke all refresh tokens for this user
        result = await self.db.execute(
            select(RefreshToken).where(
                RefreshToken.user_id == user_id,
                RefreshToken.is_revoked == False,
            )
        )
        tokens = result.scalars().all()

        for token in tokens:
            token.is_revoked = True

        await self.db.commit()
