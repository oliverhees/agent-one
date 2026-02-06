"""Security utilities unit tests."""

from datetime import datetime, timedelta
import pytest
import jwt

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_token,
)
from app.core.config import settings
from fastapi import HTTPException


class TestPasswordHashing:
    """Tests for password hashing functions."""

    def test_hash_password(self):
        """Test that hash_password returns a bcrypt hash."""
        password = "MySecurePassword123"
        hashed = hash_password(password)

        # Bcrypt hashes start with $2b$ and are 60 characters
        assert isinstance(hashed, str)
        assert hashed.startswith("$2b$")
        assert len(hashed) == 60

        # Hash should be different from original password
        assert hashed != password

    def test_hash_password_different_each_time(self):
        """Test that hashing the same password twice produces different hashes (salt)."""
        password = "SamePassword123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        # Hashes should be different due to random salt
        assert hash1 != hash2

    def test_verify_password_correct(self):
        """Test verifying a correct password."""
        password = "CorrectPassword123"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_wrong(self):
        """Test verifying an incorrect password."""
        password = "CorrectPassword123"
        wrong_password = "WrongPassword123"
        hashed = hash_password(password)

        assert verify_password(wrong_password, hashed) is False

    def test_verify_password_empty(self):
        """Test verifying with empty password."""
        password = "SomePassword123"
        hashed = hash_password(password)

        assert verify_password("", hashed) is False


class TestJWTTokens:
    """Tests for JWT token creation and verification."""

    def test_create_access_token(self):
        """Test creating an access token."""
        user_id = "test-user-id-123"
        token = create_access_token(data={"sub": user_id})

        # Token should be a non-empty string
        assert isinstance(token, str)
        assert len(token) > 0

        # Decode and verify payload
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )

        assert payload["sub"] == user_id
        assert payload["type"] == "access"
        assert "exp" in payload

        # Check expiration time (should be ~15 minutes)
        exp_time = datetime.utcfromtimestamp(payload["exp"])
        now = datetime.utcnow()
        time_diff = (exp_time - now).total_seconds()

        # Should be around 15 minutes (with some tolerance)
        expected_seconds = settings.jwt_access_token_expire_minutes * 60
        assert abs(time_diff - expected_seconds) < 5  # 5 seconds tolerance

    def test_create_refresh_token(self):
        """Test creating a refresh token."""
        user_id = "test-user-id-456"
        token = create_refresh_token(data={"sub": user_id})

        # Token should be a non-empty string
        assert isinstance(token, str)
        assert len(token) > 0

        # Decode and verify payload
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )

        assert payload["sub"] == user_id
        assert payload["type"] == "refresh"
        assert "exp" in payload

        # Check expiration time (should be ~7 days)
        exp_time = datetime.utcfromtimestamp(payload["exp"])
        now = datetime.utcnow()
        time_diff = (exp_time - now).total_seconds()

        # Should be around 7 days (with some tolerance)
        expected_seconds = settings.jwt_refresh_token_expire_days * 24 * 60 * 60
        assert abs(time_diff - expected_seconds) < 5  # 5 seconds tolerance

    def test_verify_token_valid_access(self):
        """Test verifying a valid access token."""
        user_id = "verify-test-user"
        token = create_access_token(data={"sub": user_id})

        payload = verify_token(token, token_type="access")

        assert payload["sub"] == user_id
        assert payload["type"] == "access"

    def test_verify_token_valid_refresh(self):
        """Test verifying a valid refresh token."""
        user_id = "verify-test-user"
        token = create_refresh_token(data={"sub": user_id})

        payload = verify_token(token, token_type="refresh")

        assert payload["sub"] == user_id
        assert payload["type"] == "refresh"

    def test_verify_token_wrong_type(self):
        """Test verifying token with wrong type."""
        user_id = "test-user"
        access_token = create_access_token(data={"sub": user_id})

        # Try to verify access token as refresh token
        with pytest.raises(HTTPException) as exc_info:
            verify_token(access_token, token_type="refresh")

        assert exc_info.value.status_code == 401
        assert "token type" in exc_info.value.detail.lower()

    def test_verify_token_expired(self):
        """Test verifying an expired token."""
        # Create a token that expired 1 hour ago
        expired_token = jwt.encode(
            {
                "sub": "test-user",
                "type": "access",
                "exp": datetime.utcnow() - timedelta(hours=1),
            },
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
        )

        with pytest.raises(HTTPException) as exc_info:
            verify_token(expired_token, token_type="access")

        assert exc_info.value.status_code == 401

    def test_verify_token_invalid_signature(self):
        """Test verifying a token with invalid signature."""
        # Create a token with wrong secret key
        invalid_token = jwt.encode(
            {
                "sub": "test-user",
                "type": "access",
                "exp": datetime.utcnow() + timedelta(minutes=15),
            },
            "wrong-secret-key",
            algorithm=settings.jwt_algorithm,
        )

        with pytest.raises(HTTPException) as exc_info:
            verify_token(invalid_token, token_type="access")

        assert exc_info.value.status_code == 401

    def test_verify_token_malformed(self):
        """Test verifying a malformed token."""
        malformed_token = "this.is.not.a.valid.jwt"

        with pytest.raises(HTTPException) as exc_info:
            verify_token(malformed_token, token_type="access")

        assert exc_info.value.status_code == 401


class TestTokenEdgeCases:
    """Tests for edge cases in token handling."""

    def test_token_with_additional_claims(self):
        """Test creating and verifying token with additional custom claims."""
        token = create_access_token(
            data={
                "sub": "user-123",
                "custom_field": "custom_value",
                "role": "admin",
            }
        )

        payload = verify_token(token, token_type="access")

        assert payload["sub"] == "user-123"
        assert payload["custom_field"] == "custom_value"
        assert payload["role"] == "admin"

    def test_empty_token_string(self):
        """Test verifying an empty token string."""
        with pytest.raises(HTTPException) as exc_info:
            verify_token("", token_type="access")

        assert exc_info.value.status_code == 401
