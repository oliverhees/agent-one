"""Authentication endpoint tests."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.auth import AuthService


class TestRegister:
    """Tests for /api/v1/auth/register endpoint."""

    async def test_register_success(self, client: AsyncClient):
        """Test successful user registration."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "SecurePass123",
                "display_name": "New User",
            },
        )

        assert response.status_code == 201
        data = response.json()

        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert isinstance(data["access_token"], str)
        assert isinstance(data["refresh_token"], str)
        assert len(data["access_token"]) > 0
        assert len(data["refresh_token"]) > 0

    async def test_register_duplicate_email(
        self,
        client: AsyncClient,
        test_user_credentials: dict[str, str],
    ):
        """Test registration with already registered email."""
        # Register first user
        await client.post("/api/v1/auth/register", json=test_user_credentials)

        # Try to register again with same email
        response = await client.post("/api/v1/auth/register", json=test_user_credentials)

        assert response.status_code == 409
        data = response.json()
        assert "detail" in data
        assert "already registered" in data["detail"].lower()

    async def test_register_invalid_email(self, client: AsyncClient):
        """Test registration with invalid email format."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "not-an-email",
                "password": "SecurePass123",
                "display_name": "Test User",
            },
        )

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    async def test_register_weak_password_too_short(self, client: AsyncClient):
        """Test registration with password that is too short."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "Short1",  # Less than 8 characters
                "display_name": "Test User",
            },
        )

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    async def test_register_weak_password_no_uppercase(self, client: AsyncClient):
        """Test registration with password missing uppercase letter."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "nocapital123",  # No uppercase
                "display_name": "Test User",
            },
        )

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        # Check that error mentions uppercase requirement
        error_text = str(data["detail"]).lower()
        assert "uppercase" in error_text

    async def test_register_weak_password_no_number(self, client: AsyncClient):
        """Test registration with password missing number."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "NoNumberPass",  # No number
                "display_name": "Test User",
            },
        )

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        # Check that error mentions number requirement
        error_text = str(data["detail"]).lower()
        assert "number" in error_text or "digit" in error_text

    async def test_register_missing_fields(self, client: AsyncClient):
        """Test registration with missing required fields."""
        # Missing password
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "display_name": "Test User",
            },
        )
        assert response.status_code == 422

        # Missing email
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "password": "SecurePass123",
                "display_name": "Test User",
            },
        )
        assert response.status_code == 422

        # Missing display_name
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "SecurePass123",
            },
        )
        assert response.status_code == 422


class TestLogin:
    """Tests for /api/v1/auth/login endpoint."""

    async def test_login_success(
        self,
        client: AsyncClient,
        test_user: tuple[dict, str, str],
        test_user_credentials: dict[str, str],
    ):
        """Test successful login."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user_credentials["email"],
                "password": test_user_credentials["password"],
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_wrong_password(
        self,
        client: AsyncClient,
        test_user: tuple[dict, str, str],
        test_user_credentials: dict[str, str],
    ):
        """Test login with incorrect password."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user_credentials["email"],
                "password": "WrongPassword123",
            },
        )

        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    async def test_login_nonexistent_email(self, client: AsyncClient):
        """Test login with email that doesn't exist."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "SomePassword123",
            },
        )

        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    async def test_login_missing_fields(self, client: AsyncClient):
        """Test login with missing required fields."""
        # Missing password
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com"},
        )
        assert response.status_code == 422

        # Missing email
        response = await client.post(
            "/api/v1/auth/login",
            json={"password": "SecurePass123"},
        )
        assert response.status_code == 422


class TestTokenRefresh:
    """Tests for /api/v1/auth/refresh endpoint."""

    async def test_refresh_success(
        self,
        client: AsyncClient,
        test_user: tuple[dict, str, str],
    ):
        """Test successful token refresh."""
        _, _, refresh_token = test_user

        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )

        assert response.status_code == 200
        data = response.json()

        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        # New tokens should be different from old ones
        assert data["refresh_token"] != refresh_token

    async def test_refresh_invalid_token(self, client: AsyncClient):
        """Test refresh with invalid token."""
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid.token.here"},
        )

        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    async def test_refresh_expired_token(self, client: AsyncClient):
        """Test refresh with expired token."""
        # Create a token that expired immediately
        from app.core.security import create_refresh_token
        from datetime import datetime, timedelta
        import jwt
        from app.core.config import settings

        expired_token = jwt.encode(
            {
                "sub": "some-user-id",
                "type": "refresh",
                "exp": datetime.utcnow() - timedelta(days=1),  # Expired 1 day ago
            },
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
        )

        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": expired_token},
        )

        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    async def test_refresh_revoked_token(
        self,
        client: AsyncClient,
        test_user: tuple[dict, str, str],
    ):
        """Test refresh with token that has been revoked (used once)."""
        _, _, refresh_token = test_user

        # Use refresh token once
        response1 = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert response1.status_code == 200

        # Try to use the same token again (token rotation - old token should be revoked)
        response2 = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )

        assert response2.status_code == 401
        data = response2.json()
        assert "detail" in data


class TestLogout:
    """Tests for /api/v1/auth/logout endpoint."""

    async def test_logout_success(self, authenticated_client: AsyncClient):
        """Test successful logout."""
        response = await authenticated_client.post("/api/v1/auth/logout")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data

    async def test_logout_unauthenticated(self, client: AsyncClient):
        """Test logout without authentication."""
        response = await client.post("/api/v1/auth/logout")

        assert response.status_code == 403  # HTTPBearer returns 403

    async def test_logout_invalid_token(self, client: AsyncClient):
        """Test logout with invalid token."""
        client.headers["Authorization"] = "Bearer invalid.token.here"
        response = await client.post("/api/v1/auth/logout")

        assert response.status_code == 401


class TestGetMe:
    """Tests for /api/v1/auth/me endpoint."""

    async def test_me_success(
        self,
        authenticated_client: AsyncClient,
        test_user: tuple[dict, str, str],
    ):
        """Test successful get current user."""
        user_dict, _, _ = test_user

        response = await authenticated_client.get("/api/v1/auth/me")

        assert response.status_code == 200
        data = response.json()

        assert "id" in data
        assert "email" in data
        assert "display_name" in data
        assert "is_active" in data
        assert "created_at" in data
        assert "updated_at" in data

        assert data["email"] == user_dict["email"]
        assert data["display_name"] == user_dict["display_name"]
        assert data["is_active"] is True

        # Password should NOT be in response
        assert "password" not in data
        assert "password_hash" not in data

    async def test_me_unauthenticated(self, client: AsyncClient):
        """Test get current user without authentication."""
        response = await client.get("/api/v1/auth/me")

        assert response.status_code == 403  # HTTPBearer returns 403

    async def test_me_invalid_token(self, client: AsyncClient):
        """Test get current user with invalid token."""
        client.headers["Authorization"] = "Bearer invalid.token.here"
        response = await client.get("/api/v1/auth/me")

        assert response.status_code == 401
