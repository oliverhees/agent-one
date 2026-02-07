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
from app.schemas.dashboard import DashboardSummaryResponse
from app.schemas.gamification import (
    AchievementListResponse,
    AchievementResponse,
    GamificationStatsResponse,
    XPHistoryEntry,
    XPHistoryResponse,
)
from app.schemas.nudge import (
    NudgeAcknowledgeResponse,
    NudgeHistoryItem,
    NudgeHistoryResponse,
    NudgeListResponse,
    NudgeResponse,
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
from app.schemas.settings import ADHSSettingsResponse, ADHSSettingsUpdate
from app.schemas.task import (
    TaskCompleteResponse,
    TaskCreate,
    TaskResponse,
    TaskUpdate,
)
from app.schemas.task_breakdown import (
    BreakdownConfirmRequest,
    BreakdownConfirmResponse,
    BreakdownResponse,
    BreakdownSuggestedSubtask,
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
    # Phase 3: Gamification
    "GamificationStatsResponse",
    "XPHistoryEntry",
    "XPHistoryResponse",
    "AchievementResponse",
    "AchievementListResponse",
    # Phase 3: Nudges
    "NudgeResponse",
    "NudgeListResponse",
    "NudgeAcknowledgeResponse",
    "NudgeHistoryItem",
    "NudgeHistoryResponse",
    # Phase 3: Dashboard
    "DashboardSummaryResponse",
    # Phase 3: Settings
    "ADHSSettingsResponse",
    "ADHSSettingsUpdate",
    # Phase 3: Task Breakdown
    "BreakdownResponse",
    "BreakdownSuggestedSubtask",
    "BreakdownConfirmRequest",
    "BreakdownConfirmResponse",
]
