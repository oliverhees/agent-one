"""Tests for BrainDumpService."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4


class TestParseBrainDump:
    def test_splits_by_und(self):
        from app.services.brain_dump import BrainDumpService
        items = BrainDumpService._parse_text("Einkaufen gehen und Arzt anrufen")
        assert len(items) == 2
        assert "Einkaufen gehen" in items
        assert "Arzt anrufen" in items

    def test_splits_by_newline(self):
        from app.services.brain_dump import BrainDumpService
        items = BrainDumpService._parse_text("Einkaufen\nArzt anrufen\nSport")
        assert len(items) == 3

    def test_splits_by_comma(self):
        from app.services.brain_dump import BrainDumpService
        items = BrainDumpService._parse_text("Einkaufen, Arzt, Sport")
        assert len(items) == 3

    def test_strips_whitespace(self):
        from app.services.brain_dump import BrainDumpService
        items = BrainDumpService._parse_text("  Einkaufen  ,  Arzt  ")
        assert items[0] == "Einkaufen"

    def test_removes_empty(self):
        from app.services.brain_dump import BrainDumpService
        items = BrainDumpService._parse_text("Einkaufen,,, Arzt")
        assert len(items) == 2

    def test_single_item(self):
        from app.services.brain_dump import BrainDumpService
        items = BrainDumpService._parse_text("Einkaufen gehen")
        assert len(items) == 1
        assert items[0] == "Einkaufen gehen"

    def test_numbered_list(self):
        from app.services.brain_dump import BrainDumpService
        items = BrainDumpService._parse_text("1. Einkaufen\n2. Arzt\n3. Sport")
        assert len(items) == 3
        assert items[0] == "Einkaufen"


@pytest.mark.asyncio
class TestProcessBrainDump:
    async def test_creates_tasks(self):
        from app.services.brain_dump import BrainDumpService
        mock_db = AsyncMock()
        service = BrainDumpService(mock_db)
        result = await service.process(str(uuid4()), "Einkaufen, Arzt anrufen")
        assert result["tasks_created"] == 2
        assert len(result["tasks"]) == 2
        assert mock_db.add.call_count == 2
