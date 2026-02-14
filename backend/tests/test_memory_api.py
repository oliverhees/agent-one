"""Tests for Memory API endpoints.

These tests do NOT require a running database -- all DB fixtures from
conftest.py are overridden with no-op versions.  Tests verify that routes
are correctly registered and that endpoint logic delegates to MemoryService.
"""

import asyncio
from datetime import datetime, timezone
from typing import Generator
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.schemas.memory import MemorySettingsUpdate


# ---------------------------------------------------------------------------
# Override DB fixtures from conftest.py
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Override session-scoped event loop for this test module."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
def clean_tables():
    """No-op override: Memory API tests don't need database cleanup."""
    yield


@pytest.fixture(scope="session")
def setup_db():
    """No-op override: Memory API tests don't need database setup."""
    yield


# ---------------------------------------------------------------------------
# Route Registration Tests
# ---------------------------------------------------------------------------


class TestMemoryEndpointsExist:
    """Verify memory endpoints are correctly registered on the router."""

    def test_router_has_status_endpoint(self):
        from app.api.v1.memory import router

        paths = [r.path for r in router.routes]
        assert "/status" in paths

    def test_router_has_export_endpoint(self):
        from app.api.v1.memory import router

        paths = [r.path for r in router.routes]
        assert "/export" in paths

    def test_router_has_delete_endpoint(self):
        from app.api.v1.memory import router

        routes_with_methods = [
            r for r in router.routes if hasattr(r, "methods")
        ]
        assert any(
            r.path == "" and "DELETE" in r.methods
            for r in routes_with_methods
        )

    def test_router_has_settings_endpoint(self):
        from app.api.v1.memory import router

        paths = [r.path for r in router.routes]
        assert "/settings" in paths

    def test_status_endpoint_is_get(self):
        from app.api.v1.memory import router

        routes_with_methods = [
            r for r in router.routes if hasattr(r, "methods")
        ]
        status_routes = [r for r in routes_with_methods if r.path == "/status"]
        assert len(status_routes) == 1
        assert "GET" in status_routes[0].methods

    def test_export_endpoint_is_get(self):
        from app.api.v1.memory import router

        routes_with_methods = [
            r for r in router.routes if hasattr(r, "methods")
        ]
        export_routes = [r for r in routes_with_methods if r.path == "/export"]
        assert len(export_routes) == 1
        assert "GET" in export_routes[0].methods

    def test_settings_endpoint_is_put(self):
        from app.api.v1.memory import router

        routes_with_methods = [
            r for r in router.routes if hasattr(r, "methods")
        ]
        settings_routes = [r for r in routes_with_methods if r.path == "/settings"]
        assert len(settings_routes) == 1
        assert "PUT" in settings_routes[0].methods


class TestMemoryRouterInV1:
    """Verify the memory router is registered in the v1 router."""

    def test_memory_prefix_registered(self):
        from app.api.v1.router import router as v1_router

        # Collect all route paths (sub-routers expand into full paths)
        all_paths = []
        for route in v1_router.routes:
            if hasattr(route, "path"):
                all_paths.append(route.path)
        # Memory routes should appear with /memory prefix
        assert any("/memory" in path for path in all_paths)


# ---------------------------------------------------------------------------
# Endpoint Logic Tests (mocked dependencies)
# ---------------------------------------------------------------------------


class TestGetMemoryStatus:
    """Test the GET /status endpoint logic."""

    async def test_returns_status_response(self):
        from app.api.v1.memory import get_memory_status

        mock_user = MagicMock()
        mock_user.id = uuid4()
        mock_db = AsyncMock()

        mock_status = {
            "enabled": True,
            "total_episodes": 5,
            "total_entities": 42,
            "last_analysis_at": datetime.now(timezone.utc),
        }

        with patch("app.api.v1.memory.get_graphiti_client") as mock_get_graphiti, \
             patch("app.api.v1.memory.MemoryService") as MockService:
            mock_service_instance = AsyncMock()
            mock_service_instance.get_status = AsyncMock(return_value=mock_status)
            MockService.return_value = mock_service_instance

            result = await get_memory_status(current_user=mock_user, db=mock_db)

            assert result.enabled is True
            assert result.total_episodes == 5
            assert result.total_entities == 42
            mock_service_instance.get_status.assert_called_once_with(str(mock_user.id))

    async def test_returns_disabled_status(self):
        from app.api.v1.memory import get_memory_status

        mock_user = MagicMock()
        mock_user.id = uuid4()
        mock_db = AsyncMock()

        mock_status = {
            "enabled": False,
            "total_episodes": 0,
            "total_entities": 0,
            "last_analysis_at": None,
        }

        with patch("app.api.v1.memory.get_graphiti_client"), \
             patch("app.api.v1.memory.MemoryService") as MockService:
            mock_service_instance = AsyncMock()
            mock_service_instance.get_status = AsyncMock(return_value=mock_status)
            MockService.return_value = mock_service_instance

            result = await get_memory_status(current_user=mock_user, db=mock_db)

            assert result.enabled is False
            assert result.total_episodes == 0
            assert result.total_entities == 0
            assert result.last_analysis_at is None


class TestExportMemory:
    """Test the GET /export endpoint logic."""

    async def test_returns_export_data(self):
        from app.api.v1.memory import export_memory

        mock_user = MagicMock()
        mock_user.id = uuid4()
        mock_db = AsyncMock()

        now = datetime.now(timezone.utc)
        mock_export = {
            "entities": [{"fact": "User likes coffee"}],
            "relations": [],
            "pattern_logs": [],
            "exported_at": now,
        }

        with patch("app.api.v1.memory.get_graphiti_client"), \
             patch("app.api.v1.memory.MemoryService") as MockService:
            mock_service_instance = AsyncMock()
            mock_service_instance.export_user_data = AsyncMock(return_value=mock_export)
            MockService.return_value = mock_service_instance

            result = await export_memory(current_user=mock_user, db=mock_db)

            assert result["entities"] == [{"fact": "User likes coffee"}]
            assert result["relations"] == []
            assert result["pattern_logs"] == []
            assert result["exported_at"] == now.isoformat()
            mock_service_instance.export_user_data.assert_called_once_with(str(mock_user.id))


class TestDeleteMemory:
    """Test the DELETE / endpoint logic."""

    async def test_returns_deleted_true(self):
        from app.api.v1.memory import delete_memory

        mock_user = MagicMock()
        mock_user.id = uuid4()
        mock_db = AsyncMock()

        with patch("app.api.v1.memory.get_graphiti_client"), \
             patch("app.api.v1.memory.MemoryService") as MockService:
            mock_service_instance = AsyncMock()
            mock_service_instance.delete_user_data = AsyncMock(return_value=True)
            MockService.return_value = mock_service_instance

            result = await delete_memory(current_user=mock_user, db=mock_db)

            assert result == {"deleted": True}
            mock_service_instance.delete_user_data.assert_called_once_with(str(mock_user.id))
            mock_db.commit.assert_called_once()

    async def test_returns_deleted_false_on_failure(self):
        from app.api.v1.memory import delete_memory

        mock_user = MagicMock()
        mock_user.id = uuid4()
        mock_db = AsyncMock()

        with patch("app.api.v1.memory.get_graphiti_client"), \
             patch("app.api.v1.memory.MemoryService") as MockService:
            mock_service_instance = AsyncMock()
            mock_service_instance.delete_user_data = AsyncMock(return_value=False)
            MockService.return_value = mock_service_instance

            result = await delete_memory(current_user=mock_user, db=mock_db)

            assert result == {"deleted": False}


class TestUpdateMemorySettings:
    """Test the PUT /settings endpoint logic."""

    async def test_updates_settings(self):
        from app.api.v1.memory import update_memory_settings

        mock_user = MagicMock()
        mock_user.id = uuid4()
        mock_db = AsyncMock()

        data = MemorySettingsUpdate(enabled=False)

        mock_user_settings = MagicMock()
        mock_user_settings.settings = {"adhs_mode": True}

        with patch("app.services.settings.SettingsService") as MockSettings:
            mock_settings_instance = MagicMock()
            mock_settings_instance._get_or_create_settings = AsyncMock(
                return_value=mock_user_settings
            )
            MockSettings.return_value = mock_settings_instance

            result = await update_memory_settings(
                data=data, current_user=mock_user, db=mock_db
            )

            assert result == {"enabled": False}
            assert mock_user_settings.settings["memory_enabled"] is False
            mock_db.flush.assert_called_once()
            mock_db.commit.assert_called_once()

    async def test_enables_memory(self):
        from app.api.v1.memory import update_memory_settings

        mock_user = MagicMock()
        mock_user.id = uuid4()
        mock_db = AsyncMock()

        data = MemorySettingsUpdate(enabled=True)

        mock_user_settings = MagicMock()
        mock_user_settings.settings = {}

        with patch("app.services.settings.SettingsService") as MockSettings:
            mock_settings_instance = MagicMock()
            mock_settings_instance._get_or_create_settings = AsyncMock(
                return_value=mock_user_settings
            )
            MockSettings.return_value = mock_settings_instance

            result = await update_memory_settings(
                data=data, current_user=mock_user, db=mock_db
            )

            assert result == {"enabled": True}
            assert mock_user_settings.settings["memory_enabled"] is True

    async def test_handles_none_settings(self):
        from app.api.v1.memory import update_memory_settings

        mock_user = MagicMock()
        mock_user.id = uuid4()
        mock_db = AsyncMock()

        data = MemorySettingsUpdate(enabled=True)

        mock_user_settings = MagicMock()
        mock_user_settings.settings = None

        with patch("app.services.settings.SettingsService") as MockSettings:
            mock_settings_instance = MagicMock()
            mock_settings_instance._get_or_create_settings = AsyncMock(
                return_value=mock_user_settings
            )
            MockSettings.return_value = mock_settings_instance

            result = await update_memory_settings(
                data=data, current_user=mock_user, db=mock_db
            )

            assert result == {"enabled": True}
            assert mock_user_settings.settings["memory_enabled"] is True
