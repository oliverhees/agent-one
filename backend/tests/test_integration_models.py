"""Tests for Phase 10 integration models."""
import pytest
from app.models.calendar_event import CalendarEvent
from app.models.reminder import Reminder, ReminderSource, ReminderStatus, ReminderRecurrence
from app.models.webhook import WebhookConfig, WebhookLog, WebhookDirection
from app.models.n8n_workflow import N8nWorkflow


class TestCalendarEventModel:
    def test_tablename(self):
        assert CalendarEvent.__tablename__ == "calendar_events"


class TestReminderModel:
    def test_reminder_source_enum(self):
        assert ReminderSource.MANUAL == "manual"
        assert ReminderSource.CHAT == "chat"
        assert ReminderSource.CALENDAR == "calendar"

    def test_reminder_status_enum(self):
        assert ReminderStatus.PENDING == "pending"
        assert ReminderStatus.SENT == "sent"
        assert ReminderStatus.DISMISSED == "dismissed"
        assert ReminderStatus.SNOOZED == "snoozed"

    def test_reminder_recurrence_enum(self):
        assert ReminderRecurrence.DAILY == "daily"
        assert ReminderRecurrence.WEEKLY == "weekly"
        assert ReminderRecurrence.MONTHLY == "monthly"


class TestWebhookModels:
    def test_webhook_direction_enum(self):
        assert WebhookDirection.INCOMING == "incoming"
        assert WebhookDirection.OUTGOING == "outgoing"

    def test_webhook_config_tablename(self):
        assert WebhookConfig.__tablename__ == "webhook_configs"

    def test_webhook_log_tablename(self):
        assert WebhookLog.__tablename__ == "webhook_logs"


class TestN8nWorkflowModel:
    def test_tablename(self):
        assert N8nWorkflow.__tablename__ == "n8n_workflows"
