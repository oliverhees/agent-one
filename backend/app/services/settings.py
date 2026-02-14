"""Settings service for managing ADHS-specific user settings."""

from uuid import UUID

from cryptography.fernet import InvalidToken
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import attributes

from app.core.encryption import encrypt_value, decrypt_value, mask_api_key
from app.core.modules import ALL_MODULES, DEFAULT_ACTIVE_MODULES, ALWAYS_ACTIVE_MODULES, VALID_MODULE_NAMES
from app.models.user_settings import UserSettings, DEFAULT_SETTINGS
from app.schemas.modules import ModuleInfoResponse, ModulesResponse, ModulesUpdate, ModuleConfigUpdate
from app.schemas.settings import (
    ADHSSettingsResponse,
    ADHSSettingsUpdate,
    ApiKeyUpdate,
    ApiKeyResponse,
    VoiceProviderUpdate,
    VoiceProviderResponse,
)


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
            display_name=merged.get("display_name"),
            onboarding_complete=merged.get("onboarding_complete", False),
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
            display_name=current_settings.get("display_name"),
            onboarding_complete=current_settings.get("onboarding_complete", False),
        )

    async def complete_onboarding(self, user_id: UUID, data: dict) -> None:
        """Complete onboarding by updating settings and marking onboarding as done."""
        user_settings = await self._get_or_create_settings(user_id)
        current_settings = {**DEFAULT_SETTINGS, **user_settings.settings}

        # Update provided settings
        for key, value in data.items():
            if value is not None:
                current_settings[key] = value

        # Always mark onboarding as complete
        current_settings["onboarding_complete"] = True

        user_settings.settings = current_settings
        await self.db.flush()

    async def save_api_keys(self, user_id: UUID, data: ApiKeyUpdate) -> ApiKeyResponse:
        """
        Save API keys (encrypted) in the user's settings JSONB blob.

        Args:
            user_id: User ID
            data: API keys to save (only provided keys are updated)

        Returns:
            ApiKeyResponse with masked keys
        """
        user_settings = await self._get_or_create_settings(user_id)
        current_settings = {**DEFAULT_SETTINGS, **user_settings.settings}

        # Get existing encrypted keys (or empty dict)
        api_keys = current_settings.get("api_keys", {})

        # Update only the provided keys
        update_data = data.model_dump(exclude_unset=True)
        for provider, plaintext_key in update_data.items():
            if plaintext_key:
                api_keys[provider] = encrypt_value(plaintext_key)

        # Write back
        current_settings["api_keys"] = api_keys
        user_settings.settings = current_settings

        # Mark JSONB column as modified (SQLAlchemy doesn't auto-detect nested dict changes)
        attributes.flag_modified(user_settings, "settings")

        await self.db.flush()

        # Return masked keys
        return await self.get_api_keys(user_id)

    async def get_api_keys(self, user_id: UUID) -> ApiKeyResponse:
        """
        Get API keys (decrypted and masked) for the authenticated user.

        Args:
            user_id: User ID

        Returns:
            ApiKeyResponse with masked keys (e.g. "...XXXX")
        """
        user_settings = await self._get_or_create_settings(user_id)
        current_settings = {**DEFAULT_SETTINGS, **user_settings.settings}
        encrypted_keys = current_settings.get("api_keys", {})

        # Decrypt and mask
        masked = {}
        for provider in ("anthropic", "openai", "elevenlabs", "deepgram"):
            encrypted = encrypted_keys.get(provider)
            if encrypted:
                try:
                    plaintext = decrypt_value(encrypted)
                    masked[provider] = mask_api_key(plaintext)
                except InvalidToken:
                    # Key corrupted or secret changed → ignore
                    masked[provider] = None
            else:
                masked[provider] = None

        # Check if system API key is configured
        from app.core.config import settings as app_settings
        system_anthropic_active = bool(app_settings.anthropic_api_key)

        return ApiKeyResponse(
            anthropic=masked["anthropic"],
            openai=masked["openai"],
            elevenlabs=masked["elevenlabs"],
            deepgram=masked["deepgram"],
            system_anthropic_active=system_anthropic_active,
        )

    async def update_voice_providers(
        self, user_id: UUID, data: VoiceProviderUpdate
    ) -> VoiceProviderResponse:
        """
        Update voice provider settings.

        Args:
            user_id: User ID
            data: Voice provider update (partial)

        Returns:
            VoiceProviderResponse
        """
        user_settings = await self._get_or_create_settings(user_id)
        current_settings = {**DEFAULT_SETTINGS, **user_settings.settings}

        # Update only provided fields
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            current_settings[key] = value

        user_settings.settings = current_settings
        attributes.flag_modified(user_settings, "settings")

        await self.db.flush()

        return VoiceProviderResponse(
            stt_provider=current_settings["stt_provider"],
            tts_provider=current_settings["tts_provider"],
        )

    async def get_voice_providers(self, user_id: UUID) -> VoiceProviderResponse:
        """
        Get voice provider settings.

        Args:
            user_id: User ID

        Returns:
            VoiceProviderResponse
        """
        user_settings = await self._get_or_create_settings(user_id)
        current_settings = {**DEFAULT_SETTINGS, **user_settings.settings}

        return VoiceProviderResponse(
            stt_provider=current_settings.get("stt_provider", "deepgram"),
            tts_provider=current_settings.get("tts_provider", "elevenlabs"),
        )

    # -----------------------------------------------------------------------
    # Module management
    # -----------------------------------------------------------------------

    async def get_modules(self, user_id: UUID) -> ModulesResponse:
        """Get all modules with their active/config state for a user.

        Args:
            user_id: User ID

        Returns:
            ModulesResponse with active_modules list and available_modules details.
        """
        user_settings = await self._get_or_create_settings(user_id)
        merged = {**DEFAULT_SETTINGS, **user_settings.settings}

        active_modules: list[str] = merged.get("active_modules", DEFAULT_ACTIVE_MODULES)
        module_configs: dict = merged.get("module_configs", {})

        available: list[ModuleInfoResponse] = []
        for name, meta in ALL_MODULES.items():
            # Effective config = default_config merged with user overrides
            effective_config = {**meta["default_config"], **module_configs.get(name, {})}
            available.append(
                ModuleInfoResponse(
                    name=name,
                    label=meta["label"],
                    icon=meta["icon"],
                    description=meta["description"],
                    active=name in active_modules,
                    config=effective_config,
                )
            )

        return ModulesResponse(
            active_modules=active_modules,
            available_modules=available,
        )

    async def update_modules(self, user_id: UUID, data: ModulesUpdate) -> ModulesResponse:
        """Update which modules are active for a user.

        Args:
            user_id: User ID
            data: ModulesUpdate with the desired active_modules list.

        Returns:
            ModulesResponse reflecting the new state.
        """
        user_settings = await self._get_or_create_settings(user_id)
        current = {**DEFAULT_SETTINGS, **user_settings.settings}

        current["active_modules"] = data.active_modules

        user_settings.settings = current
        attributes.flag_modified(user_settings, "settings")
        await self.db.flush()

        return await self.get_modules(user_id)

    async def update_module_config(
        self, user_id: UUID, module_name: str, data: ModuleConfigUpdate
    ) -> ModuleInfoResponse | None:
        """Update configuration for a single module.

        Args:
            user_id: User ID
            module_name: Name of the module to configure.
            data: ModuleConfigUpdate with config key-value pairs.

        Returns:
            ModuleInfoResponse for the updated module, or None if module_name
            is not recognised (caller should return 404).
        """
        if module_name not in VALID_MODULE_NAMES:
            return None

        user_settings = await self._get_or_create_settings(user_id)
        merged = {**DEFAULT_SETTINGS, **user_settings.settings}

        module_configs: dict = merged.get("module_configs", {})
        existing_config = module_configs.get(module_name, {})

        # Merge: default_config + existing overrides + new overrides
        meta = ALL_MODULES[module_name]
        effective_config = {**meta["default_config"], **existing_config, **data.config}

        module_configs[module_name] = effective_config
        merged["module_configs"] = module_configs

        user_settings.settings = merged
        attributes.flag_modified(user_settings, "settings")
        await self.db.flush()

        active_modules: list[str] = merged.get("active_modules", DEFAULT_ACTIVE_MODULES)

        return ModuleInfoResponse(
            name=module_name,
            label=meta["label"],
            icon=meta["icon"],
            description=meta["description"],
            active=module_name in active_modules,
            config=effective_config,
        )
