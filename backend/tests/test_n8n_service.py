"""Tests for N8nBridgeService."""
import pytest
from app.services.n8n_bridge import N8nBridgeService


class TestN8nBridgeService:
    @pytest.mark.asyncio
    async def test_list_workflows_empty(self, test_db):
        service = N8nBridgeService(test_db)
        workflows, total = await service.list_workflows("00000000-0000-0000-0000-000000000000")
        assert workflows == []
        assert total == 0

    @pytest.mark.asyncio
    async def test_get_nonexistent_workflow(self, test_db):
        service = N8nBridgeService(test_db)
        result = await service.get_workflow("00000000-0000-0000-0000-000000000000", "00000000-0000-0000-0000-000000000001")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_workflow(self, test_db):
        service = N8nBridgeService(test_db)
        result = await service.delete_workflow("00000000-0000-0000-0000-000000000000", "00000000-0000-0000-0000-000000000001")
        assert result is False
