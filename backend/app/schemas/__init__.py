"""Pydantic schemas for request/response validation."""

from app.schemas.auth import LoginRequest, TokenRefreshRequest, TokenResponse
from app.schemas.brain import (
    BrainEntryCreate,
    BrainEntryResponse,
    BrainEntryUpdate,
    BrainSearchResult,
)
from app.schemas.chat import (
    ConversationListResponse,
    ConversationResponse,
    MessageCreate,
    MessageResponse,
)
from app.schemas.personality import (
    PersonalityProfileCreate,
    PersonalityProfileResponse,
    PersonalityProfileUpdate,
    PersonalityTemplateResponse,
    TraitsSchema,
)
from app.schemas.proactive import (
    MentionedItemConvertRequest,
    MentionedItemResponse,
)
from app.schemas.task import (
    TaskCompleteResponse,
    TaskCreate,
    TaskResponse,
    TaskUpdate,
)
from app.schemas.user import UserCreate, UserResponse, UserUpdate

__all__ = [
    # Auth
    "LoginRequest",
    "TokenResponse",
    "TokenRefreshRequest",
    # User
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    # Chat
    "MessageCreate",
    "MessageResponse",
    "ConversationResponse",
    "ConversationListResponse",
    # Task
    "TaskCreate",
    "TaskUpdate",
    "TaskResponse",
    "TaskCompleteResponse",
    # Brain
    "BrainEntryCreate",
    "BrainEntryUpdate",
    "BrainEntryResponse",
    "BrainSearchResult",
    # Personality
    "PersonalityProfileCreate",
    "PersonalityProfileUpdate",
    "PersonalityProfileResponse",
    "PersonalityTemplateResponse",
    "TraitsSchema",
    # Proactive
    "MentionedItemResponse",
    "MentionedItemConvertRequest",
]
