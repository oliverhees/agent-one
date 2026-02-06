"""User schemas for request/response validation."""

from datetime import datetime
from uuid import UUID
import re

from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator


class UserCreate(BaseModel):
    """Schema for user registration."""

    email: EmailStr = Field(
        ...,
        description="User email address",
        examples=["user@example.com"],
    )

    password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="User password (min 8 characters, must contain 1 uppercase letter and 1 number)",
        examples=["SecurePass123!"],
    )

    display_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="User display name",
        examples=["John Doe"],
    )

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """
        Validate password requirements.

        Requirements:
        - Min 8 characters
        - At least 1 uppercase letter
        - At least 1 number
        """
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")

        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")

        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one number")

        return v


class UserUpdate(BaseModel):
    """Schema for updating user profile."""

    display_name: str | None = Field(
        None,
        min_length=1,
        max_length=100,
        description="User display name",
        examples=["Jane Doe"],
    )

    avatar_url: str | None = Field(
        None,
        max_length=500,
        description="URL to user avatar image",
        examples=["https://example.com/avatar.jpg"],
    )


class UserResponse(BaseModel):
    """Schema for user response (without password)."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "email": "user@example.com",
                "display_name": "John Doe",
                "avatar_url": "https://example.com/avatar.jpg",
                "is_active": True,
                "created_at": "2026-02-06T10:30:00Z",
                "updated_at": "2026-02-06T10:30:00Z",
            }
        },
    )

    id: UUID = Field(..., description="User unique identifier")
    email: EmailStr = Field(..., description="User email address")
    display_name: str = Field(..., description="User display name")
    avatar_url: str | None = Field(None, description="URL to user avatar image")
    is_active: bool = Field(..., description="Is user account active?")
    created_at: datetime = Field(..., description="Account creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
