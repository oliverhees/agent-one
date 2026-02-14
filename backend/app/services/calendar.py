"""Calendar integration service for Google Calendar."""

import logging
from datetime import datetime, timedelta, timezone, date, time
from typing import Any
from urllib.parse import urlencode
from uuid import UUID

import httpx
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import attributes

from app.core.config import settings
from app.core.encryption import encrypt_value, decrypt_value
from app.models.calendar_event import CalendarEvent
from app.models.user_settings import UserSettings, DEFAULT_SETTINGS

logger = logging.getLogger(__name__)

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_CALENDAR_API = "https://www.googleapis.com/calendar/v3"
GOOGLE_SCOPES = "https://www.googleapis.com/auth/calendar.readonly https://www.googleapis.com/auth/calendar.events"


class CalendarService:
    """Service for Google Calendar integration."""

    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def build_google_auth_url(redirect_uri: str, state: str) -> str:
        """Build Google OAuth 2.0 authorization URL."""
        params = {
            "client_id": settings.google_client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": GOOGLE_SCOPES,
            "access_type": "offline",
            "prompt": "consent",
            "state": state,
        }
        return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"

    async def exchange_code(self, user_id: str, code: str, redirect_uri: str) -> bool:
        """Exchange authorization code for tokens and store them."""
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                GOOGLE_TOKEN_URL,
                data={
                    "client_id": settings.google_client_id,
                    "client_secret": settings.google_client_secret,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": redirect_uri,
                },
            )
            if response.status_code != 200:
                logger.error("Google token exchange failed: %s", response.text)
                return False

            tokens = response.json()

        await self._store_credentials(
            user_id,
            {
                "access_token": encrypt_value(tokens["access_token"]),
                "refresh_token": encrypt_value(tokens.get("refresh_token", "")),
                "expires_at": (
                    datetime.now(timezone.utc) + timedelta(seconds=tokens.get("expires_in", 3600))
                ).isoformat(),
            },
        )
        return True

    async def disconnect(self, user_id: str) -> None:
        """Remove calendar credentials and cached events."""
        result = await self.db.execute(
            select(UserSettings).where(UserSettings.user_id == UUID(user_id))
        )
        user_settings = result.scalar_one_or_none()
        if user_settings:
            current = {**DEFAULT_SETTINGS, **user_settings.settings}
            current.pop("calendar_credentials", None)
            user_settings.settings = current
            attributes.flag_modified(user_settings, "settings")

        await self.db.execute(
            delete(CalendarEvent).where(CalendarEvent.user_id == UUID(user_id))
        )
        await self.db.flush()

    async def sync_events(self, user_id: str) -> list[dict]:
        """Sync events from Google Calendar to local cache."""
        access_token = await self._get_valid_access_token(user_id)
        if not access_token:
            return []

        now = datetime.now(timezone.utc)
        time_min = now.isoformat()
        time_max = (now + timedelta(days=14)).isoformat()

        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                f"{GOOGLE_CALENDAR_API}/calendars/primary/events",
                params={
                    "timeMin": time_min,
                    "timeMax": time_max,
                    "singleEvents": "true",
                    "orderBy": "startTime",
                    "maxResults": "100",
                },
                headers={"Authorization": f"Bearer {access_token}"},
            )
            if response.status_code != 200:
                logger.error("Google Calendar API error: %s", response.text)
                return []

            data = response.json()

        events = data.get("items", [])
        result_list = []
        uid = UUID(user_id)

        for event in events:
            start = event.get("start", {})
            end = event.get("end", {})
            is_all_day = "date" in start

            if is_all_day:
                start_dt = datetime.combine(date.fromisoformat(start["date"]), time.min, tzinfo=timezone.utc)
                end_dt = datetime.combine(date.fromisoformat(end["date"]), time.min, tzinfo=timezone.utc)
            else:
                start_dt = datetime.fromisoformat(start.get("dateTime", now.isoformat()))
                end_dt = datetime.fromisoformat(end.get("dateTime", now.isoformat()))

            stmt = pg_insert(CalendarEvent).values(
                user_id=uid,
                external_id=event["id"],
                title=event.get("summary", "(Kein Titel)"),
                description=event.get("description"),
                start_time=start_dt,
                end_time=end_dt,
                location=event.get("location"),
                is_all_day=is_all_day,
                calendar_provider="google",
                raw_data=event,
            ).on_conflict_do_update(
                index_elements=["user_id", "external_id"],
                set_={
                    "title": event.get("summary", "(Kein Titel)"),
                    "description": event.get("description"),
                    "start_time": start_dt,
                    "end_time": end_dt,
                    "location": event.get("location"),
                    "is_all_day": is_all_day,
                    "raw_data": event,
                },
            )
            await self.db.execute(stmt)
            result_list.append({"id": event["id"], "title": event.get("summary", "")})

        await self.db.flush()
        return result_list

    async def get_today_events(self, user_id: str) -> list[dict]:
        """Get today's events from cache."""
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)

        stmt = (
            select(CalendarEvent)
            .where(
                CalendarEvent.user_id == UUID(user_id),
                CalendarEvent.start_time >= today_start,
                CalendarEvent.start_time < today_end,
            )
            .order_by(CalendarEvent.start_time)
        )
        result = await self.db.execute(stmt)
        events = result.scalars().all()

        return [
            {
                "id": str(e.id),
                "title": e.title,
                "start_time": e.start_time.isoformat(),
                "end_time": e.end_time.isoformat(),
                "location": e.location,
                "is_all_day": e.is_all_day,
            }
            for e in events
        ]

    async def get_upcoming_events(self, user_id: str, hours: int = 24) -> list[dict]:
        """Get upcoming events within the next N hours."""
        now = datetime.now(timezone.utc)
        cutoff = now + timedelta(hours=hours)

        stmt = (
            select(CalendarEvent)
            .where(
                CalendarEvent.user_id == UUID(user_id),
                CalendarEvent.start_time >= now,
                CalendarEvent.start_time <= cutoff,
            )
            .order_by(CalendarEvent.start_time)
        )
        result = await self.db.execute(stmt)
        events = result.scalars().all()

        return [
            {
                "id": str(e.id),
                "title": e.title,
                "start_time": e.start_time.isoformat(),
                "end_time": e.end_time.isoformat(),
                "location": e.location,
                "is_all_day": e.is_all_day,
            }
            for e in events
        ]

    async def get_connection_status(self, user_id: str) -> dict:
        """Check if calendar is connected."""
        creds = await self._get_credentials(user_id)
        return {
            "connected": creds is not None,
            "provider": "google" if creds else None,
            "last_synced": None,
        }

    async def _store_credentials(self, user_id: str, credentials: dict) -> None:
        """Store encrypted credentials in UserSettings."""
        result = await self.db.execute(
            select(UserSettings).where(UserSettings.user_id == UUID(user_id))
        )
        user_settings = result.scalar_one_or_none()
        if not user_settings:
            user_settings = UserSettings(user_id=UUID(user_id), settings=dict(DEFAULT_SETTINGS))
            self.db.add(user_settings)
            await self.db.flush()

        current = {**DEFAULT_SETTINGS, **user_settings.settings}
        current["calendar_credentials"] = credentials
        user_settings.settings = current
        attributes.flag_modified(user_settings, "settings")
        await self.db.flush()

    async def _get_credentials(self, user_id: str) -> dict | None:
        """Get calendar credentials from UserSettings."""
        result = await self.db.execute(
            select(UserSettings).where(UserSettings.user_id == UUID(user_id))
        )
        user_settings = result.scalar_one_or_none()
        if not user_settings:
            return None
        current = {**DEFAULT_SETTINGS, **user_settings.settings}
        return current.get("calendar_credentials")

    async def _get_valid_access_token(self, user_id: str) -> str | None:
        """Get a valid access token, refreshing if needed."""
        creds = await self._get_credentials(user_id)
        if not creds:
            return None

        expires_at_str = creds.get("expires_at", "")
        if expires_at_str:
            expires_at = datetime.fromisoformat(expires_at_str)
            if datetime.now(timezone.utc) < expires_at - timedelta(minutes=5):
                return decrypt_value(creds["access_token"])

        # Refresh token
        refresh_token = decrypt_value(creds.get("refresh_token", ""))
        if not refresh_token:
            return None

        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                GOOGLE_TOKEN_URL,
                data={
                    "client_id": settings.google_client_id,
                    "client_secret": settings.google_client_secret,
                    "refresh_token": refresh_token,
                    "grant_type": "refresh_token",
                },
            )
            if response.status_code != 200:
                logger.error("Google token refresh failed: %s", response.text)
                return None

            tokens = response.json()

        new_creds = {
            "access_token": encrypt_value(tokens["access_token"]),
            "refresh_token": creds["refresh_token"],
            "expires_at": (
                datetime.now(timezone.utc) + timedelta(seconds=tokens.get("expires_in", 3600))
            ).isoformat(),
        }
        await self._store_credentials(user_id, new_creds)
        return tokens["access_token"]
