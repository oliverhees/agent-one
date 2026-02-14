"""Tests for briefing API endpoints."""

import pytest


class TestBriefingRouterRegistered:
    def test_briefing_prefix_in_v1_router(self):
        from app.api.v1.router import router
        paths = [r.path for r in router.routes]
        assert any("/briefing" in p for p in paths)


class TestBriefingEndpointsExist:
    def test_router_has_today_endpoint(self):
        from app.api.v1.briefing import router
        paths = [r.path for r in router.routes]
        assert "/today" in paths

    def test_router_has_generate_endpoint(self):
        from app.api.v1.briefing import router
        paths = [r.path for r in router.routes]
        assert "/generate" in paths

    def test_router_has_history_endpoint(self):
        from app.api.v1.briefing import router
        paths = [r.path for r in router.routes]
        assert "/history" in paths

    def test_router_has_read_endpoint(self):
        from app.api.v1.briefing import router
        paths = [r.path for r in router.routes]
        assert any("read" in p for p in paths)

    def test_router_has_brain_dump_endpoint(self):
        from app.api.v1.briefing import router
        paths = [r.path for r in router.routes]
        assert "/brain-dump" in paths

    def test_today_is_get(self):
        from app.api.v1.briefing import router
        for route in router.routes:
            if hasattr(route, "path") and route.path == "/today":
                assert "GET" in route.methods

    def test_generate_is_post(self):
        from app.api.v1.briefing import router
        for route in router.routes:
            if hasattr(route, "path") and route.path == "/generate":
                assert "POST" in route.methods

    def test_brain_dump_is_post(self):
        from app.api.v1.briefing import router
        for route in router.routes:
            if hasattr(route, "path") and route.path == "/brain-dump":
                assert "POST" in route.methods
