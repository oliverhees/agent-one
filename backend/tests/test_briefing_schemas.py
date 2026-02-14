"""Tests for briefing Pydantic schemas."""

import pytest
from datetime import datetime, date, timezone
from pydantic import ValidationError


class TestBriefingTaskItem:
    def test_valid_task_item(self):
        from app.schemas.briefing import BriefingTaskItem
        item = BriefingTaskItem(
            task_id="abc-123",
            title="Wichtige Aufgabe",
            priority="high",
            reason="Hohe Energie am Vormittag",
        )
        assert item.task_id == "abc-123"
        assert item.priority == "high"

    def test_optional_reason(self):
        from app.schemas.briefing import BriefingTaskItem
        item = BriefingTaskItem(
            task_id="abc",
            title="Test",
            priority="medium",
        )
        assert item.reason is None


class TestBriefingResponse:
    def test_valid_response(self):
        from app.schemas.briefing import BriefingResponse
        resp = BriefingResponse(
            id="uuid-here",
            briefing_date=date.today(),
            content="Guten Morgen!",
            tasks_suggested=[],
            wellbeing_snapshot={"score": 72, "zone": "green"},
            status="generated",
            read_at=None,
            created_at=datetime.now(timezone.utc),
        )
        assert resp.status == "generated"

    def test_status_validation(self):
        from app.schemas.briefing import BriefingResponse
        resp = BriefingResponse(
            id="uuid",
            briefing_date=date.today(),
            content="Test",
            tasks_suggested=[],
            wellbeing_snapshot={},
            status="read",
            read_at=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc),
        )
        assert resp.status == "read"


class TestBriefingHistoryResponse:
    def test_valid_history(self):
        from app.schemas.briefing import BriefingHistoryResponse
        history = BriefingHistoryResponse(briefings=[], days=7)
        assert history.days == 7

    def test_days_minimum(self):
        from app.schemas.briefing import BriefingHistoryResponse
        with pytest.raises(ValidationError):
            BriefingHistoryResponse(briefings=[], days=0)


class TestBrainDumpRequest:
    def test_valid_brain_dump(self):
        from app.schemas.briefing import BrainDumpRequest
        dump = BrainDumpRequest(text="Muss noch Einkaufen gehen und Arzt anrufen")
        assert len(dump.text) > 0

    def test_empty_text_rejected(self):
        from app.schemas.briefing import BrainDumpRequest
        with pytest.raises(ValidationError):
            BrainDumpRequest(text="")

    def test_max_length(self):
        from app.schemas.briefing import BrainDumpRequest
        with pytest.raises(ValidationError):
            BrainDumpRequest(text="x" * 5001)


class TestBrainDumpResponse:
    def test_valid_response(self):
        from app.schemas.briefing import BrainDumpResponse
        resp = BrainDumpResponse(
            tasks_created=2,
            tasks=[
                {"title": "Einkaufen gehen", "priority": "medium"},
                {"title": "Arzt anrufen", "priority": "high"},
            ],
            message="2 Aufgaben aus deinem Brain Dump erstellt.",
        )
        assert resp.tasks_created == 2


class TestSchemaRegistration:
    def test_schemas_in_init(self):
        from app.schemas import BriefingResponse, BrainDumpRequest
        assert BriefingResponse is not None
        assert BrainDumpRequest is not None
