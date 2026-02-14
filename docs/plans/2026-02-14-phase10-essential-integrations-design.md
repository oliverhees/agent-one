# Phase 10: Essential Integrations — Design

**Datum:** 2026-02-14
**Status:** Approved
**Milestone:** 5 — Essential Integrations
**Ansatz:** Backend-First Monolith (alle Integrationen im bestehenden FastAPI-Backend)

---

## 1. Google Calendar Integration

### 1.1 OAuth 2.0 Flow

1. User klickt "Google Calendar verbinden" in Settings > Integrationen
2. Mobile App oeffnet System-Browser mit Backend-URL `/api/v1/calendar/auth/google`
3. Backend redirected zu Google OAuth Consent Screen (Scopes: `calendar.readonly`, `calendar.events`)
4. Google redirected zurueck zum Backend Callback `/api/v1/calendar/auth/google/callback`
5. Backend speichert `access_token` + `refresh_token` verschluesselt in `UserSettings.settings.calendar_credentials`
6. Mobile App erhaelt Deep Link zurueck und zeigt Erfolg

**Token-Speicherung** nutzt die bestehenden `encrypt_value()`/`decrypt_value()` aus `app/services/settings.py`.

### 1.2 CalendarService

```
CalendarService
├── connect_google(user_id, auth_code) -> tokens
├── disconnect(user_id) -> void
├── sync_events(user_id) -> list[CalendarEvent]
├── get_today_events(user_id) -> list[CalendarEvent]
├── get_upcoming_events(user_id, hours=24) -> list[CalendarEvent]
└── _refresh_token_if_needed(user_id) -> str
```

- Sync alle 30 Minuten via Scheduler
- Events werden lokal in `CalendarEvent` Tabelle gecacht (Upsert via `external_id`)
- Token-Refresh automatisch wenn `access_token` abgelaufen

### 1.3 CalendarEvent DB Model

```
CalendarEvent
├── id: UUID (PK)
├── user_id: UUID (FK -> users)
├── external_id: String (Google Event ID, unique per user)
├── title: String
├── description: Text (nullable)
├── start_time: DateTime (UTC)
├── end_time: DateTime (UTC)
├── location: String (nullable)
├── is_all_day: Boolean (default false)
├── calendar_provider: String ("google")
├── raw_data: JSONB (original Google Event)
├── created_at: DateTime
├── updated_at: DateTime
```

### 1.4 Briefing-Integration

`BriefingService` wird erweitert: `get_today_events()` liefert heutige Termine, die im Morning Briefing als "Dein Terminplan" erscheinen. Das LLM erhaelt Termine als Kontext und kann zeitbasierte Empfehlungen geben ("Dein Meeting um 14:00 — plane eine Pause davor ein").

---

## 2. Smart Reminder System

### 2.1 Drei Quellen fuer Erinnerungen

| Quelle | Beschreibung | Beispiel |
|--------|-------------|---------|
| **Manual** | User erstellt Erinnerung direkt | "Erinnere mich um 15:00 an Medikamente" |
| **Chat-Extracted** | Alice erkennt Erinnerungen im Gespraech | "Ich muss morgen den Arzt anrufen" → Alice erstellt Reminder |
| **Calendar-Triggered** | Automatisch 30min vor Terminen | Google Calendar Event → Push 30min vorher |

### 2.2 Reminder DB Model

```
Reminder
├── id: UUID (PK)
├── user_id: UUID (FK -> users)
├── title: String
├── description: Text (nullable)
├── remind_at: DateTime (UTC)
├── source: Enum ("manual", "chat", "calendar")
├── status: Enum ("pending", "sent", "dismissed", "snoozed")
├── recurrence: Enum (nullable: "daily", "weekly", "monthly")
├── recurrence_end: DateTime (nullable)
├── linked_task_id: UUID (nullable, FK -> tasks)
├── linked_event_id: UUID (nullable, FK -> calendar_events)
├── created_at: DateTime
├── updated_at: DateTime
```

### 2.3 Scheduler-Integration

Neuer Scheduler-Step `_process_reminders()`:
- Prueft alle `pending` Reminders mit `remind_at <= now`
- Sendet Push Notification via `NotificationService`
- Setzt Status auf `sent`
- Bei `recurrence`: erstellt naechste Instanz

---

## 3. Webhook System

### 3.1 Incoming Webhooks

Externe Systeme koennen Alice-Aktionen triggern:

```
POST /api/v1/webhooks/incoming/{webhook_id}
Headers:
  X-Webhook-Signature: HMAC-SHA256(body, secret)
Body: { "event": "custom_trigger", "data": {...} }
```

- HMAC-SHA256 Signatur-Verifizierung mit pro-Webhook Secret
- Unterstuetzte Events: `create_task`, `create_reminder`, `trigger_briefing`, `custom`
- Logging in `WebhookLog` Tabelle

### 3.2 Outgoing Webhooks

Alice benachrichtigt externe Systeme bei Events:

| Event | Trigger | Payload |
|-------|---------|---------|
| `prediction_created` | Neue Prediction mit Confidence >= 0.75 | pattern_type, confidence, trigger_factors |
| `task_completed` | Task auf "done" gesetzt | task_id, title, completion_time |
| `briefing_generated` | Morning Briefing erstellt | briefing_id, date, task_count |
| `wellbeing_alert` | Wellbeing Score unter Schwellenwert | score, trend, intervention_type |

- Retry-Logik: 3 Versuche mit exponential Backoff (1s, 4s, 16s)
- Logging aller Versuche in `WebhookLog`

### 3.3 WebhookConfig DB Model

```
WebhookConfig
├── id: UUID (PK)
├── user_id: UUID (FK -> users)
├── name: String
├── url: String (Ziel-URL)
├── secret: String (HMAC Secret, encrypted)
├── direction: Enum ("incoming", "outgoing")
├── events: JSONB (Liste der Events, nur fuer outgoing)
├── is_active: Boolean (default true)
├── created_at: DateTime
├── updated_at: DateTime
```

### 3.4 WebhookLog DB Model

```
WebhookLog
├── id: UUID (PK)
├── webhook_id: UUID (FK -> webhook_configs)
├── direction: Enum ("incoming", "outgoing")
├── event_type: String
├── payload: JSONB
├── status_code: Integer (nullable)
├── response_body: Text (nullable, truncated)
├── attempt: Integer (1-3)
├── success: Boolean
├── created_at: DateTime
```

---

## 4. n8n Bridge

### 4.1 Konzept

n8n-Workflows werden als "externe Tools" registriert. Alice kann sie bei Bedarf ausfuehren.

### 4.2 N8nWorkflow DB Model

```
N8nWorkflow
├── id: UUID (PK)
├── user_id: UUID (FK -> users)
├── name: String (z.B. "Lead in CRM anlegen")
├── description: Text
├── webhook_url: String (n8n Webhook-Trigger URL)
├── input_schema: JSONB (erwartete Parameter)
├── is_active: Boolean (default true)
├── execution_count: Integer (default 0)
├── last_executed_at: DateTime (nullable)
├── created_at: DateTime
├── updated_at: DateTime
```

### 4.3 N8nBridgeService

```
N8nBridgeService
├── register_workflow(user_id, name, webhook_url, input_schema) -> N8nWorkflow
├── execute_workflow(user_id, workflow_id, input_data) -> dict
├── list_workflows(user_id) -> list[N8nWorkflow]
├── update_workflow(user_id, workflow_id, updates) -> N8nWorkflow
├── delete_workflow(user_id, workflow_id) -> void
```

- `execute_workflow()` sendet POST an `webhook_url` mit `input_data` via httpx
- Tracking via `execution_count` und `last_executed_at`
- Zukunft: Workflows als LangChain Tools exponieren fuer AI-gestuetzte Ausfuehrung

---

## 5. API Endpoints

### 5.1 Calendar

| Method | Endpoint | Beschreibung |
|--------|----------|-------------|
| GET | `/api/v1/calendar/auth/google` | OAuth Flow starten |
| GET | `/api/v1/calendar/auth/google/callback` | OAuth Callback |
| DELETE | `/api/v1/calendar/disconnect` | Calendar trennen |
| GET | `/api/v1/calendar/events` | Heutige Events |
| GET | `/api/v1/calendar/events/upcoming` | Events naechste 24h |
| POST | `/api/v1/calendar/sync` | Manueller Sync |
| GET | `/api/v1/calendar/status` | Verbindungsstatus |

### 5.2 Reminders

| Method | Endpoint | Beschreibung |
|--------|----------|-------------|
| POST | `/api/v1/reminders` | Reminder erstellen |
| GET | `/api/v1/reminders` | Alle Reminders listen |
| GET | `/api/v1/reminders/upcoming` | Anstehende Reminders |
| PUT | `/api/v1/reminders/{id}` | Reminder bearbeiten |
| DELETE | `/api/v1/reminders/{id}` | Reminder loeschen |
| POST | `/api/v1/reminders/{id}/snooze` | Reminder verschieben |
| POST | `/api/v1/reminders/{id}/dismiss` | Reminder verwerfen |

### 5.3 Webhooks

| Method | Endpoint | Beschreibung |
|--------|----------|-------------|
| POST | `/api/v1/webhooks` | Webhook erstellen |
| GET | `/api/v1/webhooks` | Alle Webhooks listen |
| PUT | `/api/v1/webhooks/{id}` | Webhook bearbeiten |
| DELETE | `/api/v1/webhooks/{id}` | Webhook loeschen |
| GET | `/api/v1/webhooks/{id}/logs` | Webhook Logs anzeigen |
| POST | `/api/v1/webhooks/incoming/{webhook_id}` | Incoming Webhook Endpoint |

### 5.4 n8n Bridge

| Method | Endpoint | Beschreibung |
|--------|----------|-------------|
| POST | `/api/v1/n8n/workflows` | Workflow registrieren |
| GET | `/api/v1/n8n/workflows` | Alle Workflows listen |
| PUT | `/api/v1/n8n/workflows/{id}` | Workflow bearbeiten |
| DELETE | `/api/v1/n8n/workflows/{id}` | Workflow loeschen |
| POST | `/api/v1/n8n/workflows/{id}/execute` | Workflow ausfuehren |

---

## 6. Mobile Screens

### 6.1 Settings > Integrationen

Neuer Abschnitt in Settings:
- Google Calendar: Verbinden/Trennen Toggle mit Status-Anzeige
- Webhooks: Liste + CRUD Dialog
- n8n Workflows: Liste + Registrierungs-Dialog

### 6.2 Calendar Tab (optional)

- Neuer Tab `calendar` mit `requiredModules: ["integrations"]`
- Tagesansicht mit Events als Cards
- Pull-to-refresh fuer manuellen Sync

### 6.3 Reminders

- In bestehendem Tasks-Tab als Section "Erinnerungen"
- Oder separater Sub-Tab in Tasks
- Erstell-Dialog mit Datum/Zeit-Picker und Wiederholungs-Optionen
- Snooze/Dismiss Aktionen auf Reminder-Cards
