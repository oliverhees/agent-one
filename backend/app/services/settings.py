"""Settings service for managing ADHS-specific user settings."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_settings import UserSettings, DEFAULT_SETTINGS
from app.schemas.settings import ADHSSettingsResponse, ADHSSettingsUpdate


class SettingsService:
    """Service for ADHS settings operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get_or_create_settings(self, user_id: UUID) -> UserSettings:
        """Get user settings, creating with defaults if they don't exist."""
        result = await self.db.execute(
            select(UserSettings).where(UserSettings.user_id == user_id)
        )
        user_settings = result.scalar_one_or_none()

        if not user_settings:
            user_settings = UserSettings(
                user_id=user_id,
                settings=dict(DEFAULT_SETTINGS),
            )
            self.db.add(user_settings)
            await self.db.flush()
            await self.db.refresh(user_settings)

        return user_settings

    async def get_settings(self, user_id: UUID) -> ADHSSettingsResponse:
        """Get ADHS settings for a user, returning defaults if none exist."""
        user_settings = await self._get_or_create_settings(user_id)
        settings = user_settings.settings

        # Merge with defaults so missing keys still have values
        merged = {**DEFAULT_SETTINGS, **settings}

        return ADHSSettingsResponse(
            adhs_mode=merged["adhs_mode"],
            nudge_intensity=merged["nudge_intensity"],
            auto_breakdown=merged["auto_breakdown"],
            gamification_enabled=merged["gamification_enabled"],
            focus_timer_minutes=merged["focus_timer_minutes"],
            quiet_hours_start=merged["quiet_hours_start"],
            quiet_hours_end=merged["quiet_hours_end"],
            preferred_reminder_times=merged["preferred_reminder_times"],
            expo_push_token=merged.get("expo_push_token"),
            notifications_enabled=merged.get("notifications_enabled", True),
        )

    async def register_push_token(self, user_id: UUID, token: str) -> None:
        """Store an Expo push token in the user's settings JSONB blob."""
        user_settings = await self._get_or_create_settings(user_id)
        current = {**DEFAULT_SETTINGS, **user_settings.settings}
        current["expo_push_token"] = token
        user_settings.settings = current
        await self.db.flush()

    async def update_settings(self, user_id: UUID, data: ADHSSettingsUpdate) -> ADHSSettingsResponse:
        """Partial update of ADHS settings."""
        user_settings = await self._get_or_create_settings(user_id)

        # Only update fields that were explicitly set
        update_data = data.model_dump(exclude_unset=True)
        current_settings = {**DEFAULT_SETTINGS, **user_settings.settings}

        for key, value in update_data.items():
            current_settings[key] = value

        # Write back to the JSONB column
        user_settings.settings = current_settings

        await self.db.flush()
        await self.db.refresh(user_settings)

        return ADHSSettingsResponse(
            adhs_mode=current_settings["adhs_mode"],
            nudge_intensity=current_settings["nudge_intensity"],
            auto_breakdown=current_settings["auto_breakdown"],
            gamification_enabled=current_settings["gamification_enabled"],
            focus_timer_minutes=current_settings["focus_timer_minutes"],
            quiet_hours_start=current_settings["quiet_hours_start"],
            quiet_hours_end=current_settings["quiet_hours_end"],
            preferred_reminder_times=current_settings["preferred_reminder_times"],
            expo_push_token=current_settings.get("expo_push_token"),
            notifications_enabled=current_settings.get("notifications_enabled", True),
        )
