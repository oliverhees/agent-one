"""Authentication schemas for request/response validation."""

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """Schema for user login."""

    email: EmailStr = Field(
        ...,
        description="User email address",
        examples=["user@example.com"],
    )

    password: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="User password",
        examples=["SecurePass123!"],
    )


class TokenResponse(BaseModel):
    """Schema for token response after login or refresh."""

    access_token: str = Field(
        ...,
        description="JWT access token (15 min TTL)",
        examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."],
    )

    refresh_token: str = Field(
        ...,
        description="JWT refresh token (7 day TTL)",
        examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."],
    )

    token_type: str = Field(
        default="bearer",
        description="Token type",
        examples=["bearer"],
    )

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
            }
        }


class TokenRefreshRequest(BaseModel):
    """Schema for token refresh."""

    refresh_token: str = Field(
        ...,
        description="Refresh token to exchange for new access token",
        examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."],
    )
