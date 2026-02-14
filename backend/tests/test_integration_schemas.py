"""Tests for Phase 10 Pydantic schemas."""
import pytest
from datetime import datetime, timezone
from pydantic import ValidationError
from app.schemas.calendar import CalendarEventResponse, CalendarStatusResponse
from app.schemas.reminder import ReminderCreate, ReminderResponse, ReminderSnoozeRequest
from app.schemas.webhook import WebhookCreate, WebhookResponse, WebhookLogResponse
from app.schemas.n8n import N8nWorkflowCreate, N8nWorkflowResponse, N8nExecuteRequest


class TestCalendarSchemas:
    def test_calendar_event_response(self):
        data = CalendarEventResponse(
            id="test-id",
            title="Meeting",
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc),
            is_all_day=False,
            calendar_provider="google",
            created_at=datetime.now(timezone.utc),
        )
        assert data.title == "Meeting"

    def test_calendar_status(self):
        data = CalendarStatusResponse(
            connected=True, provider="google", last_synced=None
        )
        assert data.connected is True


class TestReminderSchemas:
    def test_reminder_create_minimal(self):
        data = ReminderCreate(title="Test", remind_at=datetime.now(timezone.utc))
        assert data.source == "manual"

    def test_reminder_create_with_recurrence(self):
        data = ReminderCreate(
            title="Daily med", remind_at=datetime.now(timezone.utc), recurrence="daily"
        )
        assert data.recurrence == "daily"

    def test_reminder_create_invalid_recurrence(self):
        with pytest.raises(ValidationError):
            ReminderCreate(
                title="Bad",
                remind_at=datetime.now(timezone.utc),
                recurrence="every_two_days",
            )

    def test_snooze_request(self):
        data = ReminderSnoozeRequest(snooze_until=datetime.now(timezone.utc))
        assert data.snooze_until is not None


class TestWebhookSchemas:
    def test_webhook_create(self):
        data = WebhookCreate(
            name="Test Hook",
            url="https://example.com/hook",
            direction="outgoing",
            events=["task_completed"],
        )
        assert data.name == "Test Hook"

    def test_webhook_create_invalid_direction(self):
        with pytest.raises(ValidationError):
            WebhookCreate(
                name="Bad", url="https://example.com", direction="bidirectional"
            )


class TestN8nSchemas:
    def test_workflow_create(self):
        data = N8nWorkflowCreate(
            name="CRM Lead", webhook_url="https://n8n.example.com/webhook/abc"
        )
        assert data.name == "CRM Lead"

    def test_execute_request(self):
        data = N8nExecuteRequest(input_data={"name": "Test"})
        assert data.input_data["name"] == "Test"
