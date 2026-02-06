"""Custom exceptions for the ALICE application."""

from typing import Any
from fastapi import HTTPException, status


class AliceException(HTTPException):
    """Base exception for ALICE application."""

    def __init__(
        self,
        detail: str,
        code: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        headers: dict[str, str] | None = None,
    ):
        """
        Initialize ALICE exception.

        Args:
            detail: Human-readable error description
            code: Machine-readable error code
            status_code: HTTP status code
            headers: Optional HTTP headers
        """
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.code = code


# Authentication Exceptions

class AuthenticationError(AliceException):
    """Authentication failed."""

    def __init__(self, detail: str = "Invalid credentials"):
        super().__init__(
            detail=detail,
            code="INVALID_CREDENTIALS",
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": "Bearer"},
        )


class EmailAlreadyExistsError(AliceException):
    """Email address already registered."""

    def __init__(self, email: str):
        super().__init__(
            detail=f"Email address '{email}' is already registered",
            code="EMAIL_ALREADY_EXISTS",
            status_code=status.HTTP_409_CONFLICT,
        )


class InvalidTokenError(AliceException):
    """Token is invalid or expired."""

    def __init__(self, detail: str = "Token is invalid or expired"):
        super().__init__(
            detail=detail,
            code="INVALID_REFRESH_TOKEN",
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": "Bearer"},
        )


class AccountDisabledError(AliceException):
    """User account is disabled."""

    def __init__(self):
        super().__init__(
            detail="Account is disabled",
            code="ACCOUNT_DISABLED",
            status_code=status.HTTP_403_FORBIDDEN,
        )


class UnauthorizedError(AliceException):
    """User is not authorized."""

    def __init__(self, detail: str = "Not authorized"):
        super().__init__(
            detail=detail,
            code="UNAUTHORIZED",
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": "Bearer"},
        )


# Chat Exceptions

class ConversationNotFoundError(AliceException):
    """Conversation not found or doesn't belong to user."""

    def __init__(self, conversation_id: str):
        super().__init__(
            detail=f"Conversation '{conversation_id}' not found or access denied",
            code="CONVERSATION_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
        )


class AIServiceUnavailableError(AliceException):
    """AI service is unavailable."""

    def __init__(self, detail: str = "AI service is currently unavailable"):
        super().__init__(
            detail=detail,
            code="AI_SERVICE_UNAVAILABLE",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


# Validation Exceptions

class ValidationError(AliceException):
    """Input validation failed."""

    def __init__(self, detail: str):
        super().__init__(
            detail=detail,
            code="VALIDATION_ERROR",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )


# Task Exceptions

class TaskNotFoundError(AliceException):
    """Task not found or doesn't belong to user."""

    def __init__(self, task_id: str):
        super().__init__(
            detail=f"Task '{task_id}' not found or access denied",
            code="TASK_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
        )


class TaskAlreadyCompletedError(AliceException):
    """Task is already completed."""

    def __init__(self, task_id: str):
        super().__init__(
            detail=f"Task '{task_id}' is already completed",
            code="TASK_ALREADY_COMPLETED",
            status_code=status.HTTP_409_CONFLICT,
        )


# Brain Exceptions

class BrainEntryNotFoundError(AliceException):
    """Brain entry not found or doesn't belong to user."""

    def __init__(self, entry_id: str):
        super().__init__(
            detail=f"Brain entry '{entry_id}' not found or access denied",
            code="BRAIN_ENTRY_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
        )


class SearchUnavailableError(AliceException):
    """Search service is unavailable."""

    def __init__(self, detail: str = "Search service is currently unavailable"):
        super().__init__(
            detail=detail,
            code="SEARCH_UNAVAILABLE",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


# Personality Exceptions

class PersonalityProfileNotFoundError(AliceException):
    """Personality profile not found or doesn't belong to user."""

    def __init__(self, profile_id: str):
        super().__init__(
            detail=f"Personality profile '{profile_id}' not found or access denied",
            code="PERSONALITY_PROFILE_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
        )


class ActiveProfileCannotBeDeletedError(AliceException):
    """Active personality profile cannot be deleted."""

    def __init__(self):
        super().__init__(
            detail="Active personality profile cannot be deleted. Deactivate it first.",
            code="ACTIVE_PROFILE_CANNOT_BE_DELETED",
            status_code=status.HTTP_409_CONFLICT,
        )


# Proactive Exceptions

class MentionedItemNotFoundError(AliceException):
    """Mentioned item not found or doesn't belong to user."""

    def __init__(self, item_id: str):
        super().__init__(
            detail=f"Mentioned item '{item_id}' not found or access denied",
            code="MENTIONED_ITEM_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
        )


class MentionedItemAlreadyConvertedError(AliceException):
    """Mentioned item has already been converted."""

    def __init__(self, item_id: str):
        super().__init__(
            detail=f"Mentioned item '{item_id}' has already been converted",
            code="MENTIONED_ITEM_ALREADY_CONVERTED",
            status_code=status.HTTP_409_CONFLICT,
        )


# Rate Limiting Exception

class RateLimitExceededError(AliceException):
    """Rate limit exceeded."""

    def __init__(self, detail: str = "Too many requests"):
        super().__init__(
            detail=detail,
            code="RATE_LIMIT_EXCEEDED",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        )
