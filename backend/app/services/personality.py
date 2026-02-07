"""Personality service for managing personality profiles and templates."""

from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    PersonalityProfileNotFoundError,
    ActiveProfileCannotBeDeletedError,
)
from app.models.personality_profile import PersonalityProfile
from app.models.personality_template import PersonalityTemplate
from app.schemas.personality import PersonalityProfileCreate, PersonalityProfileUpdate


class PersonalityService:
    """Service for personality profile operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_profile(self, user_id: UUID, data: PersonalityProfileCreate) -> PersonalityProfile:
        """Create a new personality profile, optionally from a template."""
        traits = data.traits or {}
        rules = data.rules or []

        # If template_id is provided, copy traits and rules from template
        if data.template_id:
            template = await self._get_template(data.template_id)
            if template:
                traits = traits or template.traits
                rules = rules or template.rules

        profile = PersonalityProfile(
            user_id=user_id,
            name=data.name,
            template_id=data.template_id,
            traits=traits,
            rules=rules,
            custom_instructions=data.custom_instructions,
        )

        self.db.add(profile)
        await self.db.flush()
        await self.db.refresh(profile)

        return profile

    async def get_profiles(self, user_id: UUID) -> list[PersonalityProfile]:
        """Get all personality profiles for a user."""
        result = await self.db.execute(
            select(PersonalityProfile).where(
                PersonalityProfile.user_id == user_id
            ).order_by(PersonalityProfile.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_profile(self, profile_id: UUID, user_id: UUID) -> PersonalityProfile:
        """Get a personality profile by ID with ownership check."""
        result = await self.db.execute(
            select(PersonalityProfile).where(
                PersonalityProfile.id == profile_id,
                PersonalityProfile.user_id == user_id,
            )
        )
        profile = result.scalar_one_or_none()

        if not profile:
            raise PersonalityProfileNotFoundError(profile_id=str(profile_id))

        return profile

    async def update_profile(
        self, profile_id: UUID, user_id: UUID, data: PersonalityProfileUpdate
    ) -> PersonalityProfile:
        """Update a personality profile."""
        profile = await self.get_profile(profile_id, user_id)

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(profile, field, value)

        await self.db.flush()
        await self.db.refresh(profile)

        return profile

    async def delete_profile(self, profile_id: UUID, user_id: UUID) -> None:
        """Delete a personality profile. Active profiles cannot be deleted."""
        profile = await self.get_profile(profile_id, user_id)

        if profile.is_active:
            raise ActiveProfileCannotBeDeletedError()

        await self.db.delete(profile)
        await self.db.flush()

    async def activate_profile(self, profile_id: UUID, user_id: UUID) -> PersonalityProfile:
        """Activate a personality profile (deactivates the currently active one)."""
        profile = await self.get_profile(profile_id, user_id)

        # Deactivate currently active profile
        result = await self.db.execute(
            select(PersonalityProfile).where(
                PersonalityProfile.user_id == user_id,
                PersonalityProfile.is_active == True,
            )
        )
        current_active = result.scalar_one_or_none()

        if current_active and current_active.id != profile.id:
            current_active.is_active = False
            await self.db.flush()

        # Activate the new profile
        profile.is_active = True

        await self.db.flush()
        await self.db.refresh(profile)

        return profile

    async def get_templates(self) -> list[PersonalityTemplate]:
        """Get all available personality templates."""
        result = await self.db.execute(
            select(PersonalityTemplate).order_by(PersonalityTemplate.name)
        )
        return list(result.scalars().all())

    async def get_active_profile(self, user_id: UUID) -> PersonalityProfile | None:
        """Get the currently active personality profile for a user."""
        result = await self.db.execute(
            select(PersonalityProfile).where(
                PersonalityProfile.user_id == user_id,
                PersonalityProfile.is_active == True,
            )
        )
        return result.scalar_one_or_none()

    async def compose_system_prompt(self, user_id: UUID) -> str:
        """Build a system prompt from the active personality profile."""
        profile = await self.get_active_profile(user_id)

        if not profile:
            return "Du bist ALICE, eine hilfreiche KI-Assistentin fuer Menschen mit ADHS."

        parts = ["Du bist ALICE, eine hilfreiche KI-Assistentin fuer Menschen mit ADHS."]

        # Add traits
        if profile.traits:
            trait_descriptions = []
            traits = profile.traits

            formality = traits.get("formality", 50)
            if formality > 70:
                trait_descriptions.append("Kommuniziere formell und professionell.")
            elif formality < 30:
                trait_descriptions.append("Kommuniziere locker und ungezwungen.")

            humor = traits.get("humor", 50)
            if humor > 70:
                trait_descriptions.append("Nutze gerne Humor und lockere Sprueche.")
            elif humor < 30:
                trait_descriptions.append("Bleibe sachlich und ernst.")

            strictness = traits.get("strictness", 50)
            if strictness > 70:
                trait_descriptions.append("Sei streng und fordernd bei Aufgaben.")
            elif strictness < 30:
                trait_descriptions.append("Sei nachsichtig und verstaendnisvoll.")

            empathy = traits.get("empathy", 50)
            if empathy > 70:
                trait_descriptions.append("Zeige viel Empathie und Verstaendnis.")

            verbosity = traits.get("verbosity", 50)
            if verbosity > 70:
                trait_descriptions.append("Gib ausfuehrliche, detaillierte Antworten.")
            elif verbosity < 30:
                trait_descriptions.append("Antworte kurz und praegnant.")

            if trait_descriptions:
                parts.append("\n".join(trait_descriptions))

        # Add rules
        if profile.rules:
            rules_text = []
            for rule in profile.rules:
                if isinstance(rule, dict) and "text" in rule:
                    rules_text.append(f"- {rule['text']}")
            if rules_text:
                parts.append("Regeln:\n" + "\n".join(rules_text))

        # Add custom instructions
        if profile.custom_instructions:
            parts.append(f"Zusaetzliche Anweisungen: {profile.custom_instructions}")

        return "\n\n".join(parts)

    async def _get_template(self, template_id: UUID) -> PersonalityTemplate | None:
        """Get a personality template by ID."""
        result = await self.db.execute(
            select(PersonalityTemplate).where(PersonalityTemplate.id == template_id)
        )
        return result.scalar_one_or_none()
