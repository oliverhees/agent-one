# API Endpoints

**Version:** 2.2
**Datum:** 2026-02-14
**Base URL:** `https://api.alice-app.de/api/v1`
**Dokumentation:** Auto-generiert via FastAPI (Swagger UI unter `/docs`, ReDoc unter `/redoc`)

---

## Inhaltsverzeichnis

1. [Allgemeine Konventionen](#allgemeine-konventionen)
2. [Health Check](#health-check)
3. [Auth Endpoints](#auth-endpoints)
4. [Chat Endpoints](#chat-endpoints)
5. [Task Endpoints](#task-endpoints)
6. [Brain Endpoints](#brain-endpoints)
7. [Personality Endpoints](#personality-endpoints)
8. [Proactive Endpoints](#proactive-endpoints)
9. [Settings Endpoints](#settings-endpoints)
10. [Memory Endpoints](#memory-endpoints)
11. [Fehlercodes](#fehlercodes)
12. [Zusammenfassung](#zusammenfassung)

> **Hinweis:** Dieses Dokument spezifiziert die Endpoints fuer **Phase 1 (Foundation)** und **Phase 2 (Core Features)**. Spaetere Phasen werden ergaenzt, wenn die Implementierung ansteht.

---

## Allgemeine Konventionen

### Request Headers

| Header | Wert | Pflicht | Beschreibung |
|---|---|---|---|
| `Content-Type` | `application/json` | Ja (bei POST/PUT) | Request-Body-Format |
| `Authorization` | `Bearer <access_token>` | Ja (geschuetzte Endpoints) | JWT Access Token |
| `Accept` | `application/json` oder `text/event-stream` | Optional | Response-Format |

### Response Envelope

Alle erfolgreichen Responses sind direkt (kein Wrapper-Objekt). Fehler folgen einem einheitlichen Format:

```json
{
  "detail": "Beschreibung des Fehlers",
  "code": "ERROR_CODE",
  "timestamp": "2026-02-06T10:00:00Z",
  "path": "/api/v1/auth/login"
}
```

### Pagination

Cursor-basierte Pagination fuer alle Listen-Endpoints:

**Request:**
```
GET /api/v1/chat/conversations?cursor=<uuid>&limit=20
```

**Response:**
```json
{
  "items": [...],
  "next_cursor": "uuid-des-letzten-items-oder-null",
  "has_more": true,
  "total_count": 42
}
```

| Parameter | Typ | Default | Beschreibung |
|---|---|---|---|
| `cursor` | UUID (optional) | null | ID des letzten Items der vorherigen Seite |
| `limit` | int (optional) | 20 | Anzahl Items pro Seite (max 100) |

### Rate Limiting

Rate Limits werden via `X-RateLimit-*` Headers kommuniziert:

| Header | Beschreibung |
|---|---|
| `X-RateLimit-Limit` | Max. Anfragen im Zeitfenster |
| `X-RateLimit-Remaining` | Verbleibende Anfragen |
| `X-RateLimit-Reset` | Zeitpunkt des Resets (Unix Timestamp) |

Bei Ueberschreitung: `429 Too Many Requests`.

---

## Health Check

### `GET /health`

Prueft den Status aller Services.

**Auth:** Nicht erforderlich
**Rate Limit:** 60/min

**Response 200 OK:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2026-02-06T10:00:00Z",
  "services": {
    "database": "connected",
    "redis": "connected",
    "ai": "available"
  }
}
```

**Response 503 Service Unavailable:**
```json
{
  "status": "unhealthy",
  "version": "1.0.0",
  "timestamp": "2026-02-06T10:00:00Z",
  "services": {
    "database": "connected",
    "redis": "disconnected",
    "ai": "unavailable"
  }
}
```

---

## Auth Endpoints

Alle Auth-Endpoints sind unter `/api/v1/auth/` gruppiert.

### `POST /api/v1/auth/register`

Registriert einen neuen Benutzer.

**Auth:** Nicht erforderlich
**Rate Limit:** 5/min pro IP

**Request Body:**
```json
{
  "email": "max@example.com",
  "password": "SecurePass123",
  "display_name": "Max Mustermann"
}
```

**Request Schema (Pydantic):**

| Feld | Typ | Pflicht | Validierung | Beschreibung |
|---|---|---|---|---|
| `email` | `EmailStr` | Ja | Gueltiges E-Mail-Format | E-Mail-Adresse |
| `password` | `str` | Ja | Min 8 Zeichen, 1 Grossbuchstabe, 1 Zahl | Passwort (Klartext, wird gehasht) |
| `display_name` | `str` | Ja | Min 2, Max 100 Zeichen | Anzeigename |

**Response 201 Created:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "max@example.com",
  "display_name": "Max Mustermann",
  "avatar_url": null,
  "is_active": true,
  "created_at": "2026-02-06T10:00:00Z"
}
```

**Response Schema (Pydantic):**

| Feld | Typ | Beschreibung |
|---|---|---|
| `id` | `UUID` | Benutzer-ID |
| `email` | `str` | E-Mail-Adresse |
| `display_name` | `str` | Anzeigename |
| `avatar_url` | `str | null` | Avatar-URL |
| `is_active` | `bool` | Account aktiv |
| `created_at` | `datetime` | Erstellungszeitpunkt |

**Fehlerfaelle:**

| Status | Code | Beschreibung |
|---|---|---|
| 409 | `EMAIL_ALREADY_EXISTS` | E-Mail-Adresse bereits registriert |
| 422 | `VALIDATION_ERROR` | Validierungsfehler (Passwort zu kurz, E-Mail ungueltig, etc.) |
| 429 | `RATE_LIMIT_EXCEEDED` | Zu viele Registrierungsversuche |

---

### `POST /api/v1/auth/login`

Authentifiziert einen Benutzer und gibt JWT Token-Paar zurueck.

**Auth:** Nicht erforderlich
**Rate Limit:** 5/min pro IP

**Request Body:**
```json
{
  "email": "max@example.com",
  "password": "SecurePass123"
}
```

**Request Schema:**

| Feld | Typ | Pflicht | Beschreibung |
|---|---|---|---|
| `email` | `EmailStr` | Ja | E-Mail-Adresse |
| `password` | `str` | Ja | Passwort |

**Response 200 OK:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 900,
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "max@example.com",
    "display_name": "Max Mustermann",
    "avatar_url": null,
    "is_active": true,
    "created_at": "2026-02-06T10:00:00Z"
  }
}
```

**Response Schema:**

| Feld | Typ | Beschreibung |
|---|---|---|
| `access_token` | `str` | JWT Access Token (15 Minuten TTL) |
| `refresh_token` | `str` | JWT Refresh Token (7 Tage TTL) |
| `token_type` | `str` | Immer `"bearer"` |
| `expires_in` | `int` | Access Token Lebensdauer in Sekunden (900) |
| `user` | `UserResponse` | Benutzerprofil |

**Fehlerfaelle:**

| Status | Code | Beschreibung |
|---|---|---|
| 401 | `INVALID_CREDENTIALS` | Falsche E-Mail oder falsches Passwort |
| 403 | `ACCOUNT_DISABLED` | Account ist deaktiviert |
| 429 | `RATE_LIMIT_EXCEEDED` | Zu viele Login-Versuche |

---

### `POST /api/v1/auth/refresh`

Erneuert ein abgelaufenes Access Token mittels Refresh Token. Implementiert Token-Rotation.

**Auth:** Nicht erforderlich (Token im Body)
**Rate Limit:** 10/min pro IP

**Request Body:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Request Schema:**

| Feld | Typ | Pflicht | Beschreibung |
|---|---|---|---|
| `refresh_token` | `str` | Ja | Gueltiger Refresh Token |

**Response 200 OK:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 900
}
```

**Response Schema:**

| Feld | Typ | Beschreibung |
|---|---|---|
| `access_token` | `str` | Neuer JWT Access Token |
| `refresh_token` | `str` | Neuer JWT Refresh Token (Rotation!) |
| `token_type` | `str` | Immer `"bearer"` |
| `expires_in` | `int` | Access Token Lebensdauer in Sekunden |

**Fehlerfaelle:**

| Status | Code | Beschreibung |
|---|---|---|
| 401 | `INVALID_REFRESH_TOKEN` | Refresh Token ungueltig, abgelaufen oder bereits verwendet |

**Hinweis zur Token-Rotation:**
Nach erfolgreicher Nutzung wird der alte Refresh Token invalidiert und ein neuer ausgestellt. Dies verhindert Token-Replay-Angriffe.

---

### `POST /api/v1/auth/logout`

Invalidiert das aktuelle Token-Paar.

**Auth:** Bearer Token erforderlich
**Rate Limit:** 10/min

**Request Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Request Schema:**

| Feld | Typ | Pflicht | Beschreibung |
|---|---|---|---|
| `refresh_token` | `str` | Optional | Refresh Token zum Invalidieren |

**Response 204 No Content:**
Kein Response Body.

**Verhalten:**
1. Access Token wird zur Redis-Blacklist hinzugefuegt (TTL = Restlaufzeit).
2. Refresh Token (falls angegeben) wird aus Redis geloescht.
3. Alle nachfolgenden Anfragen mit diesem Access Token werden abgelehnt.

**Fehlerfaelle:**

| Status | Code | Beschreibung |
|---|---|---|
| 401 | `UNAUTHORIZED` | Kein oder ungueltiger Access Token |

---

### `GET /api/v1/auth/me`

Gibt das Profil des aktuell authentifizierten Benutzers zurueck.

**Auth:** Bearer Token erforderlich
**Rate Limit:** 60/min

**Response 200 OK:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "max@example.com",
  "display_name": "Max Mustermann",
  "avatar_url": null,
  "is_active": true,
  "timezone": "Europe/Berlin",
  "preferences": {
    "adhs_mode_enabled": true,
    "nudge_intensity": "medium",
    "theme": "system"
  },
  "created_at": "2026-02-06T10:00:00Z",
  "updated_at": "2026-02-06T10:00:00Z"
}
```

**Response Schema:**

| Feld | Typ | Beschreibung |
|---|---|---|
| `id` | `UUID` | Benutzer-ID |
| `email` | `str` | E-Mail-Adresse |
| `display_name` | `str` | Anzeigename |
| `avatar_url` | `str | null` | Avatar-URL |
| `is_active` | `bool` | Account aktiv |
| `timezone` | `str` | Zeitzone |
| `preferences` | `dict` | Nutzer-Einstellungen |
| `created_at` | `datetime` | Erstellungszeitpunkt |
| `updated_at` | `datetime` | Letzter Update |

**Fehlerfaelle:**

| Status | Code | Beschreibung |
|---|---|---|
| 401 | `UNAUTHORIZED` | Kein oder ungueltiger Access Token |

---

## Chat Endpoints

Alle Chat-Endpoints sind unter `/api/v1/chat/` gruppiert. Alle erfordern Authentifizierung.

### `POST /api/v1/chat/message`

Sendet eine Nachricht an ALICE und erhaelt eine Streaming-Antwort via Server-Sent Events (SSE).

**Auth:** Bearer Token erforderlich
**Rate Limit:** 10/min (AI-Endpoint)
**Response Format:** `text/event-stream` (SSE)

**Request Body:**
```json
{
  "message": "Hallo ALICE, was steht heute an?",
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Request Schema:**

| Feld | Typ | Pflicht | Validierung | Beschreibung |
|---|---|---|---|---|
| `message` | `str` | Ja | Min 1, Max 10000 Zeichen | Nachrichteninhalt |
| `conversation_id` | `UUID` | Nein | Muss existieren und dem User gehoeren | Konversations-ID (null = neue Konversation) |

**Response 200 OK (SSE Stream):**

```
event: conversation
data: {"conversation_id": "550e8400-e29b-41d4-a716-446655440000", "is_new": false}

event: token
data: {"content": "Guten", "index": 0}

event: token
data: {"content": " Morgen", "index": 1}

event: token
data: {"content": " Max", "index": 2}

event: token
data: {"content": "!", "index": 3}

event: token
data: {"content": " Heute", "index": 4}

event: token
data: {"content": " hast", "index": 5}

event: token
data: {"content": " du", "index": 6}

event: token
data: {"content": " 3", "index": 7}

event: token
data: {"content": " Tasks.", "index": 8}

event: mentioned_items
data: {"items": []}

event: done
data: {"message_id": "uuid", "total_tokens": 85, "prompt_tokens": 60, "completion_tokens": 25, "duration_ms": 1200, "model": "claude-3-5-sonnet"}
```

**SSE Event-Typen:**

| Event | Data Schema | Beschreibung |
|---|---|---|
| `conversation` | `{conversation_id: UUID, is_new: bool}` | Konversations-Info (erster Event) |
| `token` | `{content: str, index: int}` | Einzelner Token der Antwort |
| `mentioned_items` | `{items: MentionedItem[]}` | Extrahierte Mentioned Items |
| `done` | `{message_id, total_tokens, prompt_tokens, completion_tokens, duration_ms, model}` | Stream abgeschlossen |
| `error` | `{detail: str, code: str}` | Fehler waehrend des Streams |

**Fehlerfaelle:**

| Status | Code | Beschreibung |
|---|---|---|
| 401 | `UNAUTHORIZED` | Kein oder ungueltiger Access Token |
| 404 | `CONVERSATION_NOT_FOUND` | conversation_id existiert nicht oder gehoert nicht dem User |
| 422 | `VALIDATION_ERROR` | Message zu lang oder leer |
| 429 | `RATE_LIMIT_EXCEEDED` | Zu viele AI-Anfragen |
| 503 | `AI_SERVICE_UNAVAILABLE` | Claude API nicht erreichbar (Fallback fehlgeschlagen) |

---

### `GET /api/v1/chat/conversations`

Gibt eine paginierte Liste aller Konversationen des Nutzers zurueck.

**Auth:** Bearer Token erforderlich
**Rate Limit:** 60/min

**Query Parameter:**

| Parameter | Typ | Default | Beschreibung |
|---|---|---|---|
| `cursor` | UUID | null | Cursor fuer Pagination |
| `limit` | int | 20 | Items pro Seite (max 100) |
| `archived` | bool | false | Archivierte Konversationen anzeigen? |

**Response 200 OK:**
```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "Tagesplanung",
      "is_archived": false,
      "last_message": {
        "content": "Guten Morgen Max! Heute hast du 3 Tasks.",
        "role": "assistant",
        "created_at": "2026-02-06T07:15:00Z"
      },
      "message_count": 12,
      "created_at": "2026-02-06T07:00:00Z",
      "updated_at": "2026-02-06T07:15:00Z"
    }
  ],
  "next_cursor": "550e8400-e29b-41d4-a716-446655440001",
  "has_more": true,
  "total_count": 42
}
```

**Response Schema:**

| Feld | Typ | Beschreibung |
|---|---|---|
| `items` | `ConversationSummary[]` | Liste der Konversationen |
| `next_cursor` | `UUID | null` | Cursor fuer naechste Seite |
| `has_more` | `bool` | Gibt es weitere Seiten? |
| `total_count` | `int` | Gesamtanzahl Konversationen |

**ConversationSummary Schema:**

| Feld | Typ | Beschreibung |
|---|---|---|
| `id` | `UUID` | Konversations-ID |
| `title` | `str | null` | Titel (auto-generiert oder manuell) |
| `is_archived` | `bool` | Archiviert? |
| `last_message` | `MessagePreview | null` | Letzte Nachricht (Vorschau) |
| `message_count` | `int` | Anzahl Nachrichten |
| `created_at` | `datetime` | Erstellungszeitpunkt |
| `updated_at` | `datetime` | Letzte Aktivitaet |

**Fehlerfaelle:**

| Status | Code | Beschreibung |
|---|---|---|
| 401 | `UNAUTHORIZED` | Kein oder ungueltiger Access Token |

---

### `GET /api/v1/chat/conversations/{conversation_id}/messages`

Gibt die Nachrichten einer bestimmten Konversation zurueck (paginiert, chronologisch).

**Auth:** Bearer Token erforderlich
**Rate Limit:** 60/min

**Path Parameter:**

| Parameter | Typ | Beschreibung |
|---|---|---|
| `conversation_id` | UUID | ID der Konversation |

**Query Parameter:**

| Parameter | Typ | Default | Beschreibung |
|---|---|---|---|
| `cursor` | UUID | null | Cursor fuer Pagination |
| `limit` | int | 50 | Items pro Seite (max 100) |
| `order` | str | `asc` | Sortierung: `asc` (aelteste zuerst) oder `desc` (neueste zuerst) |

**Response 200 OK:**
```json
{
  "items": [
    {
      "id": "msg-uuid-001",
      "role": "user",
      "content": "Hallo ALICE, was steht heute an?",
      "metadata": {},
      "token_count": null,
      "created_at": "2026-02-06T07:00:00Z"
    },
    {
      "id": "msg-uuid-002",
      "role": "assistant",
      "content": "Guten Morgen Max! Heute hast du 3 Tasks:\n\n1. **Arzttermin** (high) - faellig um 14:00\n2. **E-Mail an Chef** (medium)\n3. **Einkaufen** (low)\n\nSoll ich dir einen Tagesplan erstellen?",
      "metadata": {
        "model": "claude-3-5-sonnet",
        "total_tokens": 85,
        "agents_used": ["orchestrator", "task_manager"]
      },
      "token_count": 85,
      "created_at": "2026-02-06T07:00:02Z"
    }
  ],
  "next_cursor": "msg-uuid-003",
  "has_more": false,
  "total_count": 2
}
```

**Message Schema:**

| Feld | Typ | Beschreibung |
|---|---|---|
| `id` | `UUID` | Nachrichten-ID |
| `role` | `str` | `"user"`, `"assistant"`, oder `"system"` |
| `content` | `str` | Nachrichteninhalt (Markdown) |
| `metadata` | `dict` | Metadaten (Model, Tokens, Agents, etc.) |
| `token_count` | `int | null` | Token-Anzahl |
| `created_at` | `datetime` | Erstellungszeitpunkt |

**Fehlerfaelle:**

| Status | Code | Beschreibung |
|---|---|---|
| 401 | `UNAUTHORIZED` | Kein oder ungueltiger Access Token |
| 404 | `CONVERSATION_NOT_FOUND` | Konversation existiert nicht oder gehoert nicht dem User |

---

### `WebSocket /api/v1/chat/ws`

WebSocket-Verbindung fuer Echtzeit-Chat-Kommunikation. Alternative zum SSE-basierten POST-Endpoint.

**Auth:** Token als Query-Parameter
**URL:** `wss://api.alice-app.de/api/v1/chat/ws?token=<access_token>`

**Connection Handshake:**
1. Client oeffnet WebSocket mit `token` Query-Parameter.
2. Server validiert JWT.
3. Bei Erfolg: Verbindung steht. Bei Fehler: `1008 Policy Violation` Close Frame.

**Client-to-Server Messages:**

```json
// Nachricht senden
{
  "type": "message",
  "content": "Hallo ALICE",
  "conversation_id": "uuid-oder-null"
}

// Ping (Heartbeat)
{
  "type": "ping"
}

// Typing Indicator
{
  "type": "typing",
  "conversation_id": "uuid"
}
```

| Message Type | Felder | Beschreibung |
|---|---|---|
| `message` | `content: str`, `conversation_id: UUID?` | Chat-Nachricht senden |
| `ping` | -- | Heartbeat (alle 30s empfohlen) |
| `typing` | `conversation_id: UUID` | Nutzer tippt (fuer Zukunft) |

**Server-to-Client Messages:**

```json
// Konversations-Info
{
  "type": "conversation",
  "conversation_id": "uuid",
  "is_new": true
}

// Streaming Token
{
  "type": "token",
  "content": "Hallo",
  "index": 0
}

// Stream abgeschlossen
{
  "type": "done",
  "message_id": "uuid",
  "total_tokens": 85,
  "duration_ms": 1200
}

// Pong (Heartbeat Response)
{
  "type": "pong"
}

// Proaktive Notification (Push ueber WebSocket)
{
  "type": "notification",
  "data": {
    "type": "task_reminder",
    "title": "Arzttermin in 1 Stunde",
    "body": "Vergiss nicht deinen Termin um 14:00!",
    "deep_link": "/tasks/uuid"
  }
}

// Fehler
{
  "type": "error",
  "detail": "Message too long",
  "code": "VALIDATION_ERROR"
}
```

| Message Type | Beschreibung |
|---|---|
| `conversation` | Konversations-Info (nach `message`) |
| `token` | Einzelner Token der AI-Antwort |
| `done` | Stream abgeschlossen mit Metadaten |
| `pong` | Heartbeat-Antwort |
| `notification` | Proaktive Notification (wenn WS offen) |
| `error` | Fehlermeldung |

**Close Codes:**

| Code | Beschreibung |
|---|---|
| 1000 | Normal Closure (Client/Server) |
| 1008 | Policy Violation (Auth fehlgeschlagen) |
| 1011 | Unexpected Condition (Serverfehler) |
| 1013 | Try Again Later (Ueberlastung) |

**Reconnection-Strategie (Client):**
- Exponential Backoff: 1s, 2s, 4s, 8s, 16s, 30s (max)
- Max Reconnect-Versuche: 10
- Bei `1008`: Token refreshen, dann reconnecten
- Bei `1013`: Warten, dann reconnecten

---

## Task Endpoints

Alle Task-Endpoints sind unter `/api/v1/tasks/` gruppiert. Alle erfordern Authentifizierung.

### `POST /api/v1/tasks`

Erstellt einen neuen Task fuer den authentifizierten Benutzer.

**Auth:** Bearer Token erforderlich
**Rate Limit:** 60/min

**Request Body:**
```json
{
  "title": "Arzttermin vereinbaren",
  "description": "Hausarzt anrufen wegen Blutbild-Kontrolle",
  "priority": "high",
  "due_date": "2026-02-10T14:00:00Z",
  "tags": ["gesundheit", "telefonat"],
  "parent_id": null,
  "estimated_minutes": 15
}
```

**Request Schema:**

| Feld | Typ | Pflicht | Validierung | Beschreibung |
|---|---|---|---|---|
| `title` | `str` | Ja | Min 1, Max 500 Zeichen | Task-Titel |
| `description` | `str` | Nein | Max 5000 Zeichen | Ausfuehrliche Beschreibung |
| `priority` | `str` | Nein | `low`, `medium`, `high`, `urgent` | Prioritaet (Default: `medium`) |
| `due_date` | `datetime` | Nein | Gueltiges ISO 8601 Datum | Faelligkeitsdatum |
| `tags` | `str[]` | Nein | Max 20 Tags, je Max 50 Zeichen | Tags fuer Kategorisierung |
| `parent_id` | `UUID` | Nein | Muss existieren, dem User gehoeren, darf nicht zirkulaer sein | Eltern-Task (fuer Sub-Tasks) |
| `estimated_minutes` | `int` | Nein | Min 1, Max 1440 | Geschaetzte Dauer in Minuten |

**Response 201 Created:**
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Arzttermin vereinbaren",
  "description": "Hausarzt anrufen wegen Blutbild-Kontrolle",
  "priority": "high",
  "status": "open",
  "due_date": "2026-02-10T14:00:00Z",
  "completed_at": null,
  "xp_earned": 0,
  "parent_id": null,
  "is_recurring": false,
  "recurrence_rule": null,
  "tags": ["gesundheit", "telefonat"],
  "source": "manual",
  "source_message_id": null,
  "estimated_minutes": 15,
  "sub_tasks": [],
  "created_at": "2026-02-06T10:00:00Z",
  "updated_at": "2026-02-06T10:00:00Z"
}
```

**Response Schema (TaskResponse):**

| Feld | Typ | Beschreibung |
|---|---|---|
| `id` | `UUID` | Eindeutige Task-ID |
| `user_id` | `UUID` | Zugehoeriger Benutzer |
| `title` | `str` | Task-Titel |
| `description` | `str | null` | Ausfuehrliche Beschreibung |
| `priority` | `str` | `low`, `medium`, `high`, `urgent` |
| `status` | `str` | `open`, `in_progress`, `done`, `cancelled` |
| `due_date` | `datetime | null` | Faelligkeitsdatum |
| `completed_at` | `datetime | null` | Erledigungszeitpunkt |
| `xp_earned` | `int` | Verdiente XP bei Erledigung |
| `parent_id` | `UUID | null` | Eltern-Task-ID |
| `is_recurring` | `bool` | Wiederkehrender Task? |
| `recurrence_rule` | `str | null` | iCal RRULE |
| `tags` | `str[]` | Tags |
| `source` | `str` | `manual`, `chat_extract`, `breakdown`, `recurring` |
| `source_message_id` | `UUID | null` | Quell-Nachrichten-ID |
| `estimated_minutes` | `int | null` | Geschaetzte Dauer in Minuten |
| `sub_tasks` | `TaskResponse[]` | Sub-Tasks (nur bei Einzel-Abruf) |
| `created_at` | `datetime` | Erstellungszeitpunkt |
| `updated_at` | `datetime` | Letzter Update-Zeitpunkt |

**Fehlerfaelle:**

| Status | Code | Beschreibung |
|---|---|---|
| 401 | `UNAUTHORIZED` | Kein oder ungueltiger Access Token |
| 404 | `TASK_NOT_FOUND` | parent_id existiert nicht oder gehoert nicht dem User |
| 422 | `VALIDATION_ERROR` | Validierungsfehler (Titel leer, ungueltige Prioritaet, etc.) |
| 429 | `RATE_LIMIT_EXCEEDED` | Zu viele Anfragen |

---

### `GET /api/v1/tasks`

Gibt eine paginierte, gefilterte Liste aller Tasks des Nutzers zurueck.

**Auth:** Bearer Token erforderlich
**Rate Limit:** 60/min

**Query Parameter:**

| Parameter | Typ | Default | Beschreibung |
|---|---|---|---|
| `cursor` | UUID | null | Cursor fuer Pagination |
| `limit` | int | 20 | Items pro Seite (max 100) |
| `status` | str | null | Filter nach Status: `open`, `in_progress`, `done`, `cancelled` |
| `priority` | str | null | Filter nach Prioritaet: `low`, `medium`, `high`, `urgent` |
| `tags` | str | null | Filter nach Tags (komma-getrennt, z.B. `gesundheit,arbeit`) |
| `has_due_date` | bool | null | Filter: nur Tasks mit/ohne Faelligkeitsdatum |
| `parent_id` | UUID | null | Filter: nur Sub-Tasks eines bestimmten Parent-Tasks (null = nur Top-Level) |

**Response 200 OK:**
```json
{
  "items": [
    {
      "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "user_id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "Arzttermin vereinbaren",
      "description": "Hausarzt anrufen wegen Blutbild-Kontrolle",
      "priority": "high",
      "status": "open",
      "due_date": "2026-02-10T14:00:00Z",
      "completed_at": null,
      "xp_earned": 0,
      "parent_id": null,
      "is_recurring": false,
      "recurrence_rule": null,
      "tags": ["gesundheit", "telefonat"],
      "source": "manual",
      "source_message_id": null,
      "estimated_minutes": 15,
      "sub_tasks": [],
      "created_at": "2026-02-06T10:00:00Z",
      "updated_at": "2026-02-06T10:00:00Z"
    }
  ],
  "next_cursor": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
  "has_more": true,
  "total_count": 15
}
```

**Response Schema:** `PaginatedResponse<TaskResponse>` (siehe TaskResponse oben)

**Fehlerfaelle:**

| Status | Code | Beschreibung |
|---|---|---|
| 401 | `UNAUTHORIZED` | Kein oder ungueltiger Access Token |
| 422 | `VALIDATION_ERROR` | Ungueltiger Filter-Wert |

---

### `GET /api/v1/tasks/today`

Gibt alle Tasks des Nutzers zurueck, die heute faellig sind oder den Status `open`/`in_progress` haben und kein Faelligkeitsdatum nach heute besitzen. Sortiert nach Prioritaet (urgent > high > medium > low), dann nach Faelligkeitsdatum.

**Auth:** Bearer Token erforderlich
**Rate Limit:** 60/min

**Response 200 OK:**
```json
{
  "items": [
    {
      "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "user_id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "Arzttermin",
      "description": null,
      "priority": "high",
      "status": "open",
      "due_date": "2026-02-06T14:00:00Z",
      "completed_at": null,
      "xp_earned": 0,
      "parent_id": null,
      "is_recurring": false,
      "recurrence_rule": null,
      "tags": ["gesundheit"],
      "source": "manual",
      "source_message_id": null,
      "estimated_minutes": 60,
      "sub_tasks": [],
      "created_at": "2026-02-05T20:00:00Z",
      "updated_at": "2026-02-05T20:00:00Z"
    }
  ],
  "total_count": 3,
  "total_estimated_minutes": 105
}
```

**Response Schema:**

| Feld | Typ | Beschreibung |
|---|---|---|
| `items` | `TaskResponse[]` | Heutige Tasks, sortiert nach Prioritaet |
| `total_count` | `int` | Gesamtanzahl heutiger Tasks |
| `total_estimated_minutes` | `int` | Summe der geschaetzten Minuten |

**Fehlerfaelle:**

| Status | Code | Beschreibung |
|---|---|---|
| 401 | `UNAUTHORIZED` | Kein oder ungueltiger Access Token |

---

### `GET /api/v1/tasks/{id}`

Gibt einen einzelnen Task inkl. seiner Sub-Tasks zurueck.

**Auth:** Bearer Token erforderlich
**Rate Limit:** 60/min

**Path Parameter:**

| Parameter | Typ | Beschreibung |
|---|---|---|
| `id` | UUID | Task-ID |

**Response 200 OK:**
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Umzug vorbereiten",
  "description": "Alles fuer den Umzug am 15.03. organisieren",
  "priority": "high",
  "status": "in_progress",
  "due_date": "2026-03-15T08:00:00Z",
  "completed_at": null,
  "xp_earned": 0,
  "parent_id": null,
  "is_recurring": false,
  "recurrence_rule": null,
  "tags": ["umzug", "organisation"],
  "source": "manual",
  "source_message_id": null,
  "estimated_minutes": 480,
  "sub_tasks": [
    {
      "id": "sub-task-uuid-001",
      "user_id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "Kartons besorgen",
      "description": null,
      "priority": "medium",
      "status": "done",
      "due_date": "2026-03-01T18:00:00Z",
      "completed_at": "2026-02-28T16:30:00Z",
      "xp_earned": 25,
      "parent_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "is_recurring": false,
      "recurrence_rule": null,
      "tags": ["umzug"],
      "source": "breakdown",
      "source_message_id": null,
      "estimated_minutes": 30,
      "sub_tasks": [],
      "created_at": "2026-02-06T10:00:00Z",
      "updated_at": "2026-02-28T16:30:00Z"
    }
  ],
  "created_at": "2026-02-06T10:00:00Z",
  "updated_at": "2026-02-06T10:00:00Z"
}
```

**Fehlerfaelle:**

| Status | Code | Beschreibung |
|---|---|---|
| 401 | `UNAUTHORIZED` | Kein oder ungueltiger Access Token |
| 404 | `TASK_NOT_FOUND` | Task existiert nicht oder gehoert nicht dem User |

---

### `PUT /api/v1/tasks/{id}`

Aktualisiert einen bestehenden Task. Nur uebergebene Felder werden geaendert (Partial Update).

**Auth:** Bearer Token erforderlich
**Rate Limit:** 60/min

**Path Parameter:**

| Parameter | Typ | Beschreibung |
|---|---|---|
| `id` | UUID | Task-ID |

**Request Body:**
```json
{
  "title": "Arzttermin vereinbaren (Dr. Mueller)",
  "priority": "urgent",
  "status": "in_progress",
  "due_date": "2026-02-08T10:00:00Z",
  "tags": ["gesundheit", "telefonat", "dringend"],
  "estimated_minutes": 10
}
```

**Request Schema:**

| Feld | Typ | Pflicht | Validierung | Beschreibung |
|---|---|---|---|---|
| `title` | `str` | Nein | Min 1, Max 500 Zeichen | Neuer Task-Titel |
| `description` | `str | null` | Nein | Max 5000 Zeichen | Neue Beschreibung (null = loeschen) |
| `priority` | `str` | Nein | `low`, `medium`, `high`, `urgent` | Neue Prioritaet |
| `status` | `str` | Nein | `open`, `in_progress`, `done`, `cancelled` | Neuer Status |
| `due_date` | `datetime | null` | Nein | Gueltiges ISO 8601 Datum | Neues Faelligkeitsdatum (null = loeschen) |
| `tags` | `str[]` | Nein | Max 20 Tags, je Max 50 Zeichen | Neue Tags (ersetzt komplett) |
| `estimated_minutes` | `int | null` | Nein | Min 1, Max 1440 | Neue geschaetzte Dauer (null = loeschen) |

**Response 200 OK:** `TaskResponse` (aktualisierter Task)

**Hinweis:** Status-Aenderung zu `done` ueber diesen Endpoint vergibt **keine XP**. Fuer XP-Vergabe `POST /api/v1/tasks/{id}/complete` verwenden.

**Fehlerfaelle:**

| Status | Code | Beschreibung |
|---|---|---|
| 401 | `UNAUTHORIZED` | Kein oder ungueltiger Access Token |
| 404 | `TASK_NOT_FOUND` | Task existiert nicht oder gehoert nicht dem User |
| 422 | `VALIDATION_ERROR` | Validierungsfehler |

---

### `DELETE /api/v1/tasks/{id}`

Loescht einen Task und alle zugehoerigen Sub-Tasks (CASCADE).

**Auth:** Bearer Token erforderlich
**Rate Limit:** 60/min

**Path Parameter:**

| Parameter | Typ | Beschreibung |
|---|---|---|
| `id` | UUID | Task-ID |

**Response 204 No Content:**
Kein Response Body.

**Fehlerfaelle:**

| Status | Code | Beschreibung |
|---|---|---|
| 401 | `UNAUTHORIZED` | Kein oder ungueltiger Access Token |
| 404 | `TASK_NOT_FOUND` | Task existiert nicht oder gehoert nicht dem User |

---

### `POST /api/v1/tasks/{id}/complete`

Markiert einen Task als erledigt und berechnet XP. Aktualisiert user_stats (XP, Level, Streak). Gibt die XP-Berechnung im Response zurueck.

**Auth:** Bearer Token erforderlich
**Rate Limit:** 60/min

**Path Parameter:**

| Parameter | Typ | Beschreibung |
|---|---|---|
| `id` | UUID | Task-ID |

**Request Body:** Kein Request Body erforderlich.

**Response 200 OK:**
```json
{
  "task": {
    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "Arzttermin vereinbaren",
    "description": "Hausarzt anrufen wegen Blutbild-Kontrolle",
    "priority": "high",
    "status": "done",
    "due_date": "2026-02-10T14:00:00Z",
    "completed_at": "2026-02-06T11:30:00Z",
    "xp_earned": 75,
    "parent_id": null,
    "is_recurring": false,
    "recurrence_rule": null,
    "tags": ["gesundheit", "telefonat"],
    "source": "manual",
    "source_message_id": null,
    "estimated_minutes": 15,
    "sub_tasks": [],
    "created_at": "2026-02-06T10:00:00Z",
    "updated_at": "2026-02-06T11:30:00Z"
  },
  "xp_earned": 75,
  "xp_breakdown": {
    "base": 50,
    "on_time_bonus": 25,
    "streak_bonus": 0
  },
  "total_xp": 325,
  "level": 1,
  "level_up": false
}
```

**Response Schema:**

| Feld | Typ | Beschreibung |
|---|---|---|
| `task` | `TaskResponse` | Aktualisierter Task (status=done) |
| `xp_earned` | `int` | Verdiente XP fuer diesen Task |
| `xp_breakdown` | `object` | Aufschluesselung der XP |
| `xp_breakdown.base` | `int` | Basis-XP nach Prioritaet (low=10, medium=25, high=50, urgent=100) |
| `xp_breakdown.on_time_bonus` | `int` | Bonus fuer rechtzeitige Erledigung (base * 0.5) |
| `xp_breakdown.streak_bonus` | `int` | Streak-Bonus (base * 0.25 wenn Streak > 0) |
| `total_xp` | `int` | Neue Gesamt-XP des Nutzers |
| `level` | `int` | Aktuelles Level des Nutzers |
| `level_up` | `bool` | Hat der Nutzer ein Level-Up erreicht? |

**Fehlerfaelle:**

| Status | Code | Beschreibung |
|---|---|---|
| 401 | `UNAUTHORIZED` | Kein oder ungueltiger Access Token |
| 404 | `TASK_NOT_FOUND` | Task existiert nicht oder gehoert nicht dem User |
| 409 | `TASK_ALREADY_COMPLETED` | Task ist bereits erledigt |

---

## Brain Endpoints

Alle Brain-Endpoints sind unter `/api/v1/brain/` gruppiert. Alle erfordern Authentifizierung. Das Brain (Second Brain) speichert Wissenseintraege mit semantischer Suchfunktion ueber pgvector.

### `POST /api/v1/brain/entries`

Erstellt einen neuen Brain-Eintrag. Embedding-Generierung erfolgt asynchron im Hintergrund.

**Auth:** Bearer Token erforderlich
**Rate Limit:** 60/min

**Request Body:**
```json
{
  "title": "Wie funktioniert Spaced Repetition",
  "content": "Spaced Repetition ist eine Lernmethode, bei der Informationen in zunehmenden Zeitabstaenden wiederholt werden. Die Methode basiert auf der Vergessenskurve von Ebbinghaus...",
  "entry_type": "manual",
  "tags": ["lernen", "produktivitaet", "methoden"],
  "source_url": null
}
```

**Request Schema:**

| Feld | Typ | Pflicht | Validierung | Beschreibung |
|---|---|---|---|---|
| `title` | `str` | Ja | Min 1, Max 500 Zeichen | Titel des Eintrags |
| `content` | `str` | Ja | Min 1, Max 50000 Zeichen | Inhalt (Volltext, Markdown unterstuetzt) |
| `entry_type` | `str` | Nein | `manual`, `chat_extract`, `url_import`, `file_import`, `voice_note` | Typ des Eintrags (Default: `manual`) |
| `tags` | `str[]` | Nein | Max 30 Tags, je Max 50 Zeichen | Tags fuer Kategorisierung |
| `source_url` | `str` | Nein | Gueltige URL, Max 2000 Zeichen | Quell-URL (bei Import) |

**Response 201 Created:**
```json
{
  "id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Wie funktioniert Spaced Repetition",
  "content": "Spaced Repetition ist eine Lernmethode, bei der Informationen in zunehmenden Zeitabstaenden wiederholt werden...",
  "entry_type": "manual",
  "tags": ["lernen", "produktivitaet", "methoden"],
  "source_url": null,
  "metadata": {
    "word_count": 42,
    "language": "de"
  },
  "embedding_status": "pending",
  "created_at": "2026-02-06T10:00:00Z",
  "updated_at": "2026-02-06T10:00:00Z"
}
```

**Response Schema (BrainEntryResponse):**

| Feld | Typ | Beschreibung |
|---|---|---|
| `id` | `UUID` | Eindeutige Eintrags-ID |
| `user_id` | `UUID` | Zugehoeriger Benutzer |
| `title` | `str` | Titel des Eintrags |
| `content` | `str` | Inhalt (Volltext) |
| `entry_type` | `str` | `manual`, `chat_extract`, `url_import`, `file_import`, `voice_note` |
| `tags` | `str[]` | Tags |
| `source_url` | `str | null` | Quell-URL |
| `metadata` | `dict` | Zusaetzliche Metadaten (word_count, language, etc.) |
| `embedding_status` | `str` | `pending`, `processing`, `completed`, `failed` |
| `created_at` | `datetime` | Erstellungszeitpunkt |
| `updated_at` | `datetime` | Letzter Update-Zeitpunkt |

**Fehlerfaelle:**

| Status | Code | Beschreibung |
|---|---|---|
| 401 | `UNAUTHORIZED` | Kein oder ungueltiger Access Token |
| 422 | `VALIDATION_ERROR` | Validierungsfehler (Titel leer, Content zu lang, etc.) |
| 429 | `RATE_LIMIT_EXCEEDED` | Zu viele Anfragen |

---

### `GET /api/v1/brain/entries`

Gibt eine paginierte, gefilterte Liste aller Brain-Eintraege des Nutzers zurueck.

**Auth:** Bearer Token erforderlich
**Rate Limit:** 60/min

**Query Parameter:**

| Parameter | Typ | Default | Beschreibung |
|---|---|---|---|
| `cursor` | UUID | null | Cursor fuer Pagination |
| `limit` | int | 20 | Items pro Seite (max 100) |
| `entry_type` | str | null | Filter nach Typ: `manual`, `chat_extract`, `url_import`, `file_import`, `voice_note` |
| `tags` | str | null | Filter nach Tags (komma-getrennt, z.B. `lernen,methoden`) |

**Response 200 OK:**
```json
{
  "items": [
    {
      "id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
      "user_id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "Wie funktioniert Spaced Repetition",
      "content": "Spaced Repetition ist eine Lernmethode...",
      "entry_type": "manual",
      "tags": ["lernen", "produktivitaet", "methoden"],
      "source_url": null,
      "metadata": {
        "word_count": 42,
        "language": "de"
      },
      "embedding_status": "completed",
      "created_at": "2026-02-06T10:00:00Z",
      "updated_at": "2026-02-06T10:00:00Z"
    }
  ],
  "next_cursor": "c3d4e5f6-a7b8-9012-cdef-123456789012",
  "has_more": false,
  "total_count": 8
}
```

**Response Schema:** `PaginatedResponse<BrainEntryResponse>`

**Fehlerfaelle:**

| Status | Code | Beschreibung |
|---|---|---|
| 401 | `UNAUTHORIZED` | Kein oder ungueltiger Access Token |
| 422 | `VALIDATION_ERROR` | Ungueltiger Filter-Wert |

---

### `GET /api/v1/brain/entries/{id}`

Gibt einen einzelnen Brain-Eintrag zurueck.

**Auth:** Bearer Token erforderlich
**Rate Limit:** 60/min

**Path Parameter:**

| Parameter | Typ | Beschreibung |
|---|---|---|
| `id` | UUID | Brain-Eintrags-ID |

**Response 200 OK:** `BrainEntryResponse` (siehe oben)

**Fehlerfaelle:**

| Status | Code | Beschreibung |
|---|---|---|
| 401 | `UNAUTHORIZED` | Kein oder ungueltiger Access Token |
| 404 | `BRAIN_ENTRY_NOT_FOUND` | Eintrag existiert nicht oder gehoert nicht dem User |

---

### `PUT /api/v1/brain/entries/{id}`

Aktualisiert einen bestehenden Brain-Eintrag. Bei Aenderung des `content`-Feldes werden Embeddings neu generiert.

**Auth:** Bearer Token erforderlich
**Rate Limit:** 60/min

**Path Parameter:**

| Parameter | Typ | Beschreibung |
|---|---|---|
| `id` | UUID | Brain-Eintrags-ID |

**Request Body:**
```json
{
  "title": "Spaced Repetition -- Komplett-Guide",
  "content": "Aktualisierter Inhalt mit mehr Details...",
  "tags": ["lernen", "produktivitaet", "methoden", "spaced-repetition"]
}
```

**Request Schema:**

| Feld | Typ | Pflicht | Validierung | Beschreibung |
|---|---|---|---|---|
| `title` | `str` | Nein | Min 1, Max 500 Zeichen | Neuer Titel |
| `content` | `str` | Nein | Min 1, Max 50000 Zeichen | Neuer Inhalt (triggert Re-Embedding) |
| `tags` | `str[]` | Nein | Max 30 Tags, je Max 50 Zeichen | Neue Tags (ersetzt komplett) |
| `source_url` | `str | null` | Nein | Gueltige URL, Max 2000 Zeichen | Neue Quell-URL (null = loeschen) |

**Response 200 OK:** `BrainEntryResponse` (aktualisierter Eintrag, `embedding_status` = `pending` bei Content-Aenderung)

**Fehlerfaelle:**

| Status | Code | Beschreibung |
|---|---|---|
| 401 | `UNAUTHORIZED` | Kein oder ungueltiger Access Token |
| 404 | `BRAIN_ENTRY_NOT_FOUND` | Eintrag existiert nicht oder gehoert nicht dem User |
| 422 | `VALIDATION_ERROR` | Validierungsfehler |

---

### `DELETE /api/v1/brain/entries/{id}`

Loescht einen Brain-Eintrag und alle zugehoerigen Embeddings (CASCADE).

**Auth:** Bearer Token erforderlich
**Rate Limit:** 60/min

**Path Parameter:**

| Parameter | Typ | Beschreibung |
|---|---|---|
| `id` | UUID | Brain-Eintrags-ID |

**Response 204 No Content:**
Kein Response Body.

**Fehlerfaelle:**

| Status | Code | Beschreibung |
|---|---|---|
| 401 | `UNAUTHORIZED` | Kein oder ungueltiger Access Token |
| 404 | `BRAIN_ENTRY_NOT_FOUND` | Eintrag existiert nicht oder gehoert nicht dem User |

---

### `GET /api/v1/brain/search`

Fuehrt eine semantische Suche ueber alle Brain-Eintraege des Nutzers durch. Verwendet pgvector Cosine Similarity auf den Embeddings.

**Auth:** Bearer Token erforderlich
**Rate Limit:** 60/min

**Query Parameter:**

| Parameter | Typ | Default | Beschreibung |
|---|---|---|---|
| `q` | str | -- (Pflicht) | Suchtext (wird in Embedding umgewandelt) |
| `limit` | int | 10 | Max. Anzahl Ergebnisse (max 50) |
| `min_score` | float | 0.3 | Minimaler Similarity-Score (0.0 - 1.0) |

**Response 200 OK:**
```json
{
  "results": [
    {
      "entry": {
        "id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
        "user_id": "550e8400-e29b-41d4-a716-446655440000",
        "title": "Wie funktioniert Spaced Repetition",
        "content": "Spaced Repetition ist eine Lernmethode...",
        "entry_type": "manual",
        "tags": ["lernen", "produktivitaet", "methoden"],
        "source_url": null,
        "metadata": {
          "word_count": 42,
          "language": "de"
        },
        "embedding_status": "completed",
        "created_at": "2026-02-06T10:00:00Z",
        "updated_at": "2026-02-06T10:00:00Z"
      },
      "score": 0.87,
      "matched_chunks": [
        "Spaced Repetition ist eine Lernmethode, bei der Informationen in zunehmenden Zeitabstaenden wiederholt werden.",
        "Die Methode basiert auf der Vergessenskurve von Ebbinghaus und optimiert den Zeitpunkt der Wiederholung."
      ]
    }
  ],
  "query": "Lernmethoden fuer besseres Gedaechtnis",
  "total_results": 1
}
```

**Response Schema:**

| Feld | Typ | Beschreibung |
|---|---|---|
| `results` | `SearchResult[]` | Suchergebnisse, sortiert nach Score (absteigend) |
| `query` | `str` | Originaler Suchtext |
| `total_results` | `int` | Anzahl gefundener Ergebnisse |

**SearchResult Schema:**

| Feld | Typ | Beschreibung |
|---|---|---|
| `entry` | `BrainEntryResponse` | Der gefundene Brain-Eintrag |
| `score` | `float` | Cosine Similarity Score (0.0 - 1.0, hoeher = besser) |
| `matched_chunks` | `str[]` | Text-Chunks, die den Treffer ausgeloest haben |

**Fehlerfaelle:**

| Status | Code | Beschreibung |
|---|---|---|
| 401 | `UNAUTHORIZED` | Kein oder ungueltiger Access Token |
| 422 | `VALIDATION_ERROR` | Suchtext leer oder zu lang |
| 503 | `SEARCH_UNAVAILABLE` | Embedding-Service nicht verfuegbar |

---

## Personality Endpoints

Alle Personality-Endpoints sind unter `/api/v1/personality/` gruppiert. Alle erfordern Authentifizierung. Der Personality-Bereich ermoeglicht die Anpassung von ALICEs Persoenlichkeit ueber Profile, Traits und Rules.

### `POST /api/v1/personality/profiles`

Erstellt ein neues Persoenlichkeitsprofil. Optional basierend auf einem Template.

**Auth:** Bearer Token erforderlich
**Rate Limit:** 60/min

**Request Body:**
```json
{
  "name": "Mein Coach",
  "template_id": "tmpl-uuid-001",
  "traits": {
    "formality": 30,
    "humor": 60,
    "strictness": 50,
    "empathy": 80,
    "verbosity": 40
  },
  "rules": [
    {"text": "Sprich mich mit Du an", "enabled": true},
    {"text": "Verwende keine Emojis", "enabled": true}
  ],
  "custom_instructions": "Motiviere mich besonders morgens beim Aufstehen."
}
```

**Request Schema:**

| Feld | Typ | Pflicht | Validierung | Beschreibung |
|---|---|---|---|---|
| `name` | `str` | Ja | Min 1, Max 100 Zeichen | Profilname |
| `template_id` | `UUID` | Nein | Muss existierendes Template sein | Basierendes Template (Traits/Rules werden uebernommen und koennen ueberschrieben werden) |
| `traits` | `object` | Nein | Werte 0-100, Keys: `formality`, `humor`, `strictness`, `empathy`, `verbosity` | Persoenlichkeits-Traits als Slider-Werte |
| `rules` | `object[]` | Nein | Max 20 Rules, je Max 500 Zeichen | Custom Rules |
| `rules[].text` | `str` | Ja | Min 1, Max 500 Zeichen | Rule-Text |
| `rules[].enabled` | `bool` | Nein | -- | Rule aktiv? (Default: true) |
| `custom_instructions` | `str` | Nein | Max 2000 Zeichen | Freitext: Zusaetzliche Anweisungen |

**Response 201 Created:**
```json
{
  "id": "prof-uuid-001",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Mein Coach",
  "is_active": false,
  "template_id": "tmpl-uuid-001",
  "template_name": "Strenger Coach",
  "traits": {
    "formality": 30,
    "humor": 60,
    "strictness": 50,
    "empathy": 80,
    "verbosity": 40
  },
  "rules": [
    {"id": "rule-uuid-001", "text": "Sprich mich mit Du an", "enabled": true},
    {"id": "rule-uuid-002", "text": "Verwende keine Emojis", "enabled": true}
  ],
  "voice_style": {},
  "custom_instructions": "Motiviere mich besonders morgens beim Aufstehen.",
  "created_at": "2026-02-06T10:00:00Z",
  "updated_at": "2026-02-06T10:00:00Z"
}
```

**Response Schema (PersonalityProfileResponse):**

| Feld | Typ | Beschreibung |
|---|---|---|
| `id` | `UUID` | Eindeutige Profil-ID |
| `user_id` | `UUID` | Zugehoeriger Benutzer |
| `name` | `str` | Profilname |
| `is_active` | `bool` | Ist dieses Profil aktiv? |
| `template_id` | `UUID | null` | Basierendes Template |
| `template_name` | `str | null` | Name des Templates (fuer Anzeige) |
| `traits` | `object` | Persoenlichkeits-Traits (Slider-Werte 0-100) |
| `rules` | `object[]` | Custom Rules mit generierter ID |
| `voice_style` | `object` | Voice-Konfiguration (TTS-Parameter) |
| `custom_instructions` | `str | null` | Freitext-Anweisungen |
| `created_at` | `datetime` | Erstellungszeitpunkt |
| `updated_at` | `datetime` | Letzter Update-Zeitpunkt |

**Fehlerfaelle:**

| Status | Code | Beschreibung |
|---|---|---|
| 401 | `UNAUTHORIZED` | Kein oder ungueltiger Access Token |
| 404 | `PERSONALITY_TEMPLATE_NOT_FOUND` | template_id existiert nicht |
| 422 | `VALIDATION_ERROR` | Validierungsfehler (Name leer, ungueltige Trait-Werte, etc.) |

---

### `GET /api/v1/personality/profiles`

Gibt alle Persoenlichkeitsprofile des Nutzers zurueck.

**Auth:** Bearer Token erforderlich
**Rate Limit:** 60/min

**Response 200 OK:**
```json
{
  "items": [
    {
      "id": "prof-uuid-001",
      "user_id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Mein Coach",
      "is_active": true,
      "template_id": "tmpl-uuid-001",
      "template_name": "Strenger Coach",
      "traits": {
        "formality": 30,
        "humor": 60,
        "strictness": 50,
        "empathy": 80,
        "verbosity": 40
      },
      "rules": [
        {"id": "rule-uuid-001", "text": "Sprich mich mit Du an", "enabled": true}
      ],
      "voice_style": {},
      "custom_instructions": "Motiviere mich besonders morgens beim Aufstehen.",
      "created_at": "2026-02-06T10:00:00Z",
      "updated_at": "2026-02-06T10:00:00Z"
    }
  ],
  "total_count": 1
}
```

**Response Schema:**

| Feld | Typ | Beschreibung |
|---|---|---|
| `items` | `PersonalityProfileResponse[]` | Liste der Profile |
| `total_count` | `int` | Gesamtanzahl Profile |

**Fehlerfaelle:**

| Status | Code | Beschreibung |
|---|---|---|
| 401 | `UNAUTHORIZED` | Kein oder ungueltiger Access Token |

---

### `PUT /api/v1/personality/profiles/{id}`

Aktualisiert ein bestehendes Persoenlichkeitsprofil. Nur uebergebene Felder werden geaendert.

**Auth:** Bearer Token erforderlich
**Rate Limit:** 60/min

**Path Parameter:**

| Parameter | Typ | Beschreibung |
|---|---|---|
| `id` | UUID | Profil-ID |

**Request Body:**
```json
{
  "name": "Mein Entspannter Coach",
  "traits": {
    "formality": 20,
    "humor": 70,
    "strictness": 30,
    "empathy": 90,
    "verbosity": 50
  },
  "rules": [
    {"id": "rule-uuid-001", "text": "Sprich mich mit Du an", "enabled": true},
    {"text": "Erinnere mich an Pausen", "enabled": true}
  ],
  "custom_instructions": "Sei besonders geduldig mit mir."
}
```

**Request Schema:**

| Feld | Typ | Pflicht | Validierung | Beschreibung |
|---|---|---|---|---|
| `name` | `str` | Nein | Min 1, Max 100 Zeichen | Neuer Profilname |
| `traits` | `object` | Nein | Werte 0-100 | Neue Trait-Werte (ersetzt komplett) |
| `rules` | `object[]` | Nein | Max 20 Rules | Neue Rules (ersetzt komplett; vorhandene IDs behalten, neue bekommen generierte ID) |
| `custom_instructions` | `str | null` | Nein | Max 2000 Zeichen | Neue Freitext-Anweisungen (null = loeschen) |

**Response 200 OK:** `PersonalityProfileResponse` (aktualisiertes Profil)

**Fehlerfaelle:**

| Status | Code | Beschreibung |
|---|---|---|
| 401 | `UNAUTHORIZED` | Kein oder ungueltiger Access Token |
| 404 | `PERSONALITY_PROFILE_NOT_FOUND` | Profil existiert nicht oder gehoert nicht dem User |
| 422 | `VALIDATION_ERROR` | Validierungsfehler |

---

### `DELETE /api/v1/personality/profiles/{id}`

Loescht ein Persoenlichkeitsprofil. Das aktive Profil kann nicht geloescht werden -- es muss zuerst ein anderes Profil aktiviert werden.

**Auth:** Bearer Token erforderlich
**Rate Limit:** 60/min

**Path Parameter:**

| Parameter | Typ | Beschreibung |
|---|---|---|
| `id` | UUID | Profil-ID |

**Response 204 No Content:**
Kein Response Body.

**Fehlerfaelle:**

| Status | Code | Beschreibung |
|---|---|---|
| 401 | `UNAUTHORIZED` | Kein oder ungueltiger Access Token |
| 404 | `PERSONALITY_PROFILE_NOT_FOUND` | Profil existiert nicht oder gehoert nicht dem User |
| 409 | `ACTIVE_PROFILE_CANNOT_BE_DELETED` | Aktives Profil kann nicht geloescht werden |

---

### `POST /api/v1/personality/profiles/{id}/activate`

Aktiviert ein Persoenlichkeitsprofil. Das zuvor aktive Profil wird automatisch deaktiviert (nur ein aktives Profil pro User).

**Auth:** Bearer Token erforderlich
**Rate Limit:** 60/min

**Path Parameter:**

| Parameter | Typ | Beschreibung |
|---|---|---|
| `id` | UUID | Profil-ID |

**Request Body:** Kein Request Body erforderlich.

**Response 200 OK:**
```json
{
  "id": "prof-uuid-001",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Mein Coach",
  "is_active": true,
  "template_id": "tmpl-uuid-001",
  "template_name": "Strenger Coach",
  "traits": {
    "formality": 30,
    "humor": 60,
    "strictness": 50,
    "empathy": 80,
    "verbosity": 40
  },
  "rules": [
    {"id": "rule-uuid-001", "text": "Sprich mich mit Du an", "enabled": true}
  ],
  "voice_style": {},
  "custom_instructions": "Motiviere mich besonders morgens beim Aufstehen.",
  "created_at": "2026-02-06T10:00:00Z",
  "updated_at": "2026-02-06T12:00:00Z"
}
```

**Response Schema:** `PersonalityProfileResponse` (mit `is_active: true`)

**Fehlerfaelle:**

| Status | Code | Beschreibung |
|---|---|---|
| 401 | `UNAUTHORIZED` | Kein oder ungueltiger Access Token |
| 404 | `PERSONALITY_PROFILE_NOT_FOUND` | Profil existiert nicht oder gehoert nicht dem User |

---

### `GET /api/v1/personality/templates`

Gibt alle verfuegbaren Persoenlichkeits-Templates zurueck. Templates sind vordefiniert und gelten fuer alle User.

**Auth:** Bearer Token erforderlich
**Rate Limit:** 60/min

**Response 200 OK:**
```json
{
  "items": [
    {
      "id": "tmpl-uuid-001",
      "name": "Strenger Coach",
      "description": "Direkt, fokussiert und ergebnisorientiert. Haelt dich auf Kurs mit klaren Ansagen.",
      "traits": {
        "formality": 70,
        "humor": 20,
        "strictness": 90,
        "empathy": 40,
        "verbosity": 30
      },
      "rules": [],
      "is_default": false,
      "icon": "shield"
    },
    {
      "id": "tmpl-uuid-002",
      "name": "Freundlicher Begleiter",
      "description": "Warmherzig, ermutigend und geduldig. Begleitet dich mit Verstaendnis.",
      "traits": {
        "formality": 20,
        "humor": 70,
        "strictness": 20,
        "empathy": 90,
        "verbosity": 60
      },
      "rules": [],
      "is_default": true,
      "icon": "heart"
    },
    {
      "id": "tmpl-uuid-003",
      "name": "Sachlicher Assistent",
      "description": "Professionell, effizient und auf den Punkt. Klare Informationen ohne Umschweife.",
      "traits": {
        "formality": 80,
        "humor": 10,
        "strictness": 50,
        "empathy": 50,
        "verbosity": 40
      },
      "rules": [],
      "is_default": false,
      "icon": "briefcase"
    },
    {
      "id": "tmpl-uuid-004",
      "name": "Motivierende Cheerleaderin",
      "description": "Energetisch, positiv und feiernd. Jeder kleine Erfolg wird gefeiert!",
      "traits": {
        "formality": 10,
        "humor": 80,
        "strictness": 30,
        "empathy": 80,
        "verbosity": 70
      },
      "rules": [],
      "is_default": false,
      "icon": "star"
    }
  ],
  "total_count": 4
}
```

**Response Schema:**

| Feld | Typ | Beschreibung |
|---|---|---|
| `items` | `PersonalityTemplateResponse[]` | Liste der Templates |
| `total_count` | `int` | Gesamtanzahl Templates |

**PersonalityTemplateResponse Schema:**

| Feld | Typ | Beschreibung |
|---|---|---|
| `id` | `UUID` | Eindeutige Template-ID |
| `name` | `str` | Template-Name |
| `description` | `str` | Beschreibung des Templates |
| `traits` | `object` | Vorgegebene Trait-Werte |
| `rules` | `object[]` | Vorgegebene Rules |
| `is_default` | `bool` | Standard-Template fuer neue User? |
| `icon` | `str | null` | Icon-Bezeichnung |

**Fehlerfaelle:**

| Status | Code | Beschreibung |
|---|---|---|
| 401 | `UNAUTHORIZED` | Kein oder ungueltiger Access Token |

---

### `GET /api/v1/personality/preview`

Generiert eine kurze Vorschau-Nachricht mit dem aktuell aktiven Persoenlichkeitsprofil. Nuetzlich fuer den Personality Editor, um Aenderungen sofort zu sehen.

**Auth:** Bearer Token erforderlich
**Rate Limit:** 10/min (AI-Endpoint)

**Query Parameter:**

| Parameter | Typ | Default | Beschreibung |
|---|---|---|---|
| `message` | str | "Wie geht es dir heute?" | Test-Nachricht fuer die Vorschau |

**Response 200 OK:**
```json
{
  "preview_response": "Hey! Mir geht's super, danke der Nachfrage. Und bei dir? Hast du schon deine Tasks fuer heute gecheckt? Lass uns mal schauen, was ansteht!",
  "profile_name": "Mein Coach",
  "traits_used": {
    "formality": 30,
    "humor": 60,
    "strictness": 50,
    "empathy": 80,
    "verbosity": 40
  }
}
```

**Response Schema:**

| Feld | Typ | Beschreibung |
|---|---|---|
| `preview_response` | `str` | Generierte Vorschau-Nachricht |
| `profile_name` | `str` | Name des verwendeten Profils |
| `traits_used` | `object` | Trait-Werte, die fuer die Generierung verwendet wurden |

**Fehlerfaelle:**

| Status | Code | Beschreibung |
|---|---|---|
| 401 | `UNAUTHORIZED` | Kein oder ungueltiger Access Token |
| 404 | `PERSONALITY_PROFILE_NOT_FOUND` | Kein aktives Profil vorhanden |
| 429 | `RATE_LIMIT_EXCEEDED` | Zu viele Preview-Anfragen |
| 503 | `AI_SERVICE_UNAVAILABLE` | KI-Service nicht erreichbar |

---

## Proactive Endpoints

Alle Proactive-Endpoints sind unter `/api/v1/proactive/` gruppiert. Alle erfordern Authentifizierung. Der Proactive-Bereich verwaltet automatisch aus Chat-Nachrichten extrahierte "Mentioned Items" (Tasks, Termine, Ideen, Follow-Ups, Reminders).

### `GET /api/v1/proactive/mentioned-items`

Gibt eine paginierte Liste der Mentioned Items des Nutzers zurueck.

**Auth:** Bearer Token erforderlich
**Rate Limit:** 60/min

**Query Parameter:**

| Parameter | Typ | Default | Beschreibung |
|---|---|---|---|
| `cursor` | UUID | null | Cursor fuer Pagination |
| `limit` | int | 20 | Items pro Seite (max 100) |
| `status` | str | `pending` | Filter nach Status: `pending`, `converted`, `dismissed`, `snoozed` |
| `item_type` | str | null | Filter nach Typ: `task`, `appointment`, `idea`, `follow_up`, `reminder` |

**Response 200 OK:**
```json
{
  "items": [
    {
      "id": "mi-uuid-001",
      "user_id": "550e8400-e29b-41d4-a716-446655440000",
      "message_id": "msg-uuid-002",
      "item_type": "task",
      "content": "Arzttermin vereinbaren",
      "status": "pending",
      "extracted_data": {
        "suggested_title": "Arzttermin vereinbaren",
        "suggested_priority": "high",
        "suggested_due_date": "2026-02-10",
        "confidence": 0.92,
        "context_snippet": "Ich muss unbedingt diese Woche noch zum Arzt..."
      },
      "converted_to_id": null,
      "converted_to_type": null,
      "snoozed_until": null,
      "created_at": "2026-02-06T07:00:02Z"
    },
    {
      "id": "mi-uuid-002",
      "user_id": "550e8400-e29b-41d4-a716-446655440000",
      "message_id": "msg-uuid-002",
      "item_type": "idea",
      "content": "Meal-Prep am Sonntag ausprobieren",
      "status": "pending",
      "extracted_data": {
        "suggested_title": "Meal-Prep am Sonntag ausprobieren",
        "confidence": 0.78,
        "context_snippet": "Vielleicht sollte ich mal Meal-Prep ausprobieren..."
      },
      "converted_to_id": null,
      "converted_to_type": null,
      "snoozed_until": null,
      "created_at": "2026-02-06T07:00:02Z"
    }
  ],
  "next_cursor": null,
  "has_more": false,
  "total_count": 2
}
```

**Response Schema (MentionedItemResponse):**

| Feld | Typ | Beschreibung |
|---|---|---|
| `id` | `UUID` | Eindeutige Item-ID |
| `user_id` | `UUID` | Zugehoeriger Benutzer |
| `message_id` | `UUID` | Quell-Nachricht |
| `item_type` | `str` | `task`, `appointment`, `idea`, `follow_up`, `reminder` |
| `content` | `str` | Extrahierter Inhalt |
| `status` | `str` | `pending`, `converted`, `dismissed`, `snoozed` |
| `extracted_data` | `object` | Strukturierte extrahierte Daten (Vorschlaege, Konfidenz, Kontext) |
| `converted_to_id` | `UUID | null` | ID des erstellten Tasks/Brain-Eintrags |
| `converted_to_type` | `str | null` | `task` oder `brain_entry` |
| `snoozed_until` | `datetime | null` | Snoozed bis (wenn Status = snoozed) |
| `created_at` | `datetime` | Erstellungszeitpunkt |

**Fehlerfaelle:**

| Status | Code | Beschreibung |
|---|---|---|
| 401 | `UNAUTHORIZED` | Kein oder ungueltiger Access Token |
| 422 | `VALIDATION_ERROR` | Ungueltiger Filter-Wert |

---

### `POST /api/v1/proactive/mentioned-items/{id}/convert`

Konvertiert ein Mentioned Item in einen Task oder Brain-Eintrag. Der Status wird auf `converted` gesetzt.

**Auth:** Bearer Token erforderlich
**Rate Limit:** 60/min

**Path Parameter:**

| Parameter | Typ | Beschreibung |
|---|---|---|
| `id` | UUID | Mentioned-Item-ID |

**Request Body:**
```json
{
  "convert_to": "task",
  "task_data": {
    "title": "Arzttermin vereinbaren",
    "priority": "high",
    "due_date": "2026-02-10T14:00:00Z",
    "tags": ["gesundheit"]
  }
}
```

**Request Schema:**

| Feld | Typ | Pflicht | Validierung | Beschreibung |
|---|---|---|---|---|
| `convert_to` | `str` | Ja | `task` oder `brain_entry` | Ziel-Typ der Konvertierung |
| `task_data` | `object` | Bedingt | Pflicht wenn `convert_to = task` | Task-Daten (siehe TaskCreate Schema) |
| `brain_entry_data` | `object` | Bedingt | Pflicht wenn `convert_to = brain_entry` | Brain-Entry-Daten (siehe BrainEntryCreate Schema) |

**Response 200 OK (Konvertierung zu Task):**
```json
{
  "mentioned_item": {
    "id": "mi-uuid-001",
    "status": "converted",
    "converted_to_id": "new-task-uuid",
    "converted_to_type": "task"
  },
  "created_task": {
    "id": "new-task-uuid",
    "title": "Arzttermin vereinbaren",
    "priority": "high",
    "status": "open",
    "source": "chat_extract",
    "source_message_id": "msg-uuid-002"
  }
}
```

**Response Schema:**

| Feld | Typ | Beschreibung |
|---|---|---|
| `mentioned_item` | `MentionedItemResponse` | Aktualisiertes Mentioned Item (status=converted) |
| `created_task` | `TaskResponse` | Erstellter Task (wenn convert_to=task) |
| `created_brain_entry` | `BrainEntryResponse` | Erstellter Brain-Eintrag (wenn convert_to=brain_entry) |

**Fehlerfaelle:**

| Status | Code | Beschreibung |
|---|---|---|
| 401 | `UNAUTHORIZED` | Kein oder ungueltiger Access Token |
| 404 | `MENTIONED_ITEM_NOT_FOUND` | Item existiert nicht oder gehoert nicht dem User |
| 409 | `MENTIONED_ITEM_ALREADY_CONVERTED` | Item wurde bereits konvertiert |
| 422 | `VALIDATION_ERROR` | Validierungsfehler in den Ziel-Daten |

---

### `POST /api/v1/proactive/mentioned-items/{id}/dismiss`

Verwirft ein Mentioned Item. Der Status wird auf `dismissed` gesetzt.

**Auth:** Bearer Token erforderlich
**Rate Limit:** 60/min

**Path Parameter:**

| Parameter | Typ | Beschreibung |
|---|---|---|
| `id` | UUID | Mentioned-Item-ID |

**Request Body:** Kein Request Body erforderlich.

**Response 200 OK:**
```json
{
  "id": "mi-uuid-001",
  "status": "dismissed",
  "content": "Arzttermin vereinbaren",
  "item_type": "task"
}
```

**Fehlerfaelle:**

| Status | Code | Beschreibung |
|---|---|---|
| 401 | `UNAUTHORIZED` | Kein oder ungueltiger Access Token |
| 404 | `MENTIONED_ITEM_NOT_FOUND` | Item existiert nicht oder gehoert nicht dem User |

---

### `POST /api/v1/proactive/mentioned-items/{id}/snooze`

Snoozet ein Mentioned Item bis zu einem bestimmten Zeitpunkt. Der Status wird auf `snoozed` gesetzt.

**Auth:** Bearer Token erforderlich
**Rate Limit:** 60/min

**Path Parameter:**

| Parameter | Typ | Beschreibung |
|---|---|---|
| `id` | UUID | Mentioned-Item-ID |

**Request Body:**
```json
{
  "until": "2026-02-07T09:00:00Z"
}
```

**Request Schema:**

| Feld | Typ | Pflicht | Validierung | Beschreibung |
|---|---|---|---|---|
| `until` | `datetime` | Ja | Muss in der Zukunft liegen, max 30 Tage | Snoozed bis zu diesem Zeitpunkt |

**Response 200 OK:**
```json
{
  "id": "mi-uuid-001",
  "status": "snoozed",
  "content": "Arzttermin vereinbaren",
  "item_type": "task",
  "snoozed_until": "2026-02-07T09:00:00Z"
}
```

**Fehlerfaelle:**

| Status | Code | Beschreibung |
|---|---|---|
| 401 | `UNAUTHORIZED` | Kein oder ungueltiger Access Token |
| 404 | `MENTIONED_ITEM_NOT_FOUND` | Item existiert nicht oder gehoert nicht dem User |
| 422 | `VALIDATION_ERROR` | Zeitpunkt in der Vergangenheit oder zu weit in der Zukunft |

---

## Settings Endpoints

Die Settings Endpoints ermöglichen das Verwalten von Benutzereinstellungen, API-Keys und Voice-Provider-Konfiguration.

---

### `GET /api/v1/settings/adhs`

Ruft die ADHS-spezifischen Einstellungen des authentifizierten Benutzers ab.

**Auth:** Bearer Token erforderlich
**Rate Limit:** 60/min

**Response 200 OK:**
```json
{
  "adhs_mode": true,
  "nudge_intensity": "medium",
  "auto_breakdown": true,
  "gamification_enabled": true,
  "focus_timer_minutes": 25,
  "quiet_hours_start": "22:00",
  "quiet_hours_end": "07:00",
  "preferred_reminder_times": ["09:00", "14:00", "18:00"],
  "expo_push_token": "ExponentPushToken[xyz...]",
  "notifications_enabled": true,
  "display_name": "Max",
  "onboarding_complete": true
}
```

**Fehlerfaelle:**

| Status | Code | Beschreibung |
|---|---|---|
| 403 | `FORBIDDEN` | Kein oder ungueltiger Access Token |

---

### `PUT /api/v1/settings/adhs`

Aktualisiert ADHS-Einstellungen (partial update: nur angegebene Felder werden geaendert).

**Auth:** Bearer Token erforderlich
**Rate Limit:** 60/min

**Request Body:**
```json
{
  "nudge_intensity": "high",
  "focus_timer_minutes": 15
}
```

**Request Schema:**

| Feld | Typ | Pflicht | Validierung | Beschreibung |
|---|---|---|---|---|
| `adhs_mode` | `boolean` | Nein | - | ADHS-Modus aktiv? |
| `nudge_intensity` | `string` | Nein | `low`, `medium`, `high` | Nudge-Intensitaet |
| `auto_breakdown` | `boolean` | Nein | - | Automatischer Task-Breakdown? |
| `gamification_enabled` | `boolean` | Nein | - | Gamification aktiv? |
| `focus_timer_minutes` | `integer` | Nein | 5-120 | Focus-Timer Dauer in Minuten |
| `quiet_hours_start` | `string` | Nein | HH:MM Format | Ruhezeiten Start |
| `quiet_hours_end` | `string` | Nein | HH:MM Format | Ruhezeiten Ende |
| `preferred_reminder_times` | `array[string]` | Nein | HH:MM Format, max 10 | Bevorzugte Erinnerungszeiten |
| `notifications_enabled` | `boolean` | Nein | - | Push-Benachrichtigungen aktiv? |
| `display_name` | `string` | Nein | 1-100 Zeichen | Anzeigename |

**Response 200 OK:**
Gleiche Struktur wie GET (vollstaendiges Settings-Objekt).

**Fehlerfaelle:**

| Status | Code | Beschreibung |
|---|---|---|
| 403 | `FORBIDDEN` | Kein oder ungueltiger Access Token |
| 422 | `VALIDATION_ERROR` | Ungueltige Werte (z.B. `nudge_intensity: "extreme"`) |

---

### `POST /api/v1/settings/push-token`

Registriert oder aktualisiert das Expo Push Token fuer Push-Benachrichtigungen.

**Auth:** Bearer Token erforderlich
**Rate Limit:** 60/min

**Request Body:**
```json
{
  "expo_push_token": "ExponentPushToken[abc123...]"
}
```

**Request Schema:**

| Feld | Typ | Pflicht | Validierung | Beschreibung |
|---|---|---|---|---|
| `expo_push_token` | `string` | Ja | Min. 10 Zeichen | Expo Push Token |

**Response 204 No Content**

Kein Response Body bei Erfolg.

**Fehlerfaelle:**

| Status | Code | Beschreibung |
|---|---|---|
| 403 | `FORBIDDEN` | Kein oder ungueltiger Access Token |
| 422 | `VALIDATION_ERROR` | Token zu kurz oder ungueltig |

---

### `POST /api/v1/settings/onboarding`

Schliesst das Onboarding ab und speichert initiale Praeferenzen.

**Auth:** Bearer Token erforderlich
**Rate Limit:** 60/min

**Request Body:**
```json
{
  "display_name": "Max",
  "focus_timer_minutes": 25,
  "nudge_intensity": "medium"
}
```

**Request Schema:**

| Feld | Typ | Pflicht | Validierung | Beschreibung |
|---|---|---|---|---|
| `display_name` | `string` | Nein | 1-100 Zeichen | Anzeigename (optional) |
| `focus_timer_minutes` | `integer` | Nein | 5-120 | Focus-Timer Dauer |
| `nudge_intensity` | `string` | Nein | `low`, `medium`, `high` | Nudge-Intensitaet |

**Response 200 OK:**
```json
{
  "success": true,
  "message": "Onboarding abgeschlossen"
}
```

**Fehlerfaelle:**

| Status | Code | Beschreibung |
|---|---|---|
| 403 | `FORBIDDEN` | Kein oder ungueltiger Access Token |
| 422 | `VALIDATION_ERROR` | Ungueltige Werte |

---

### `GET /api/v1/settings/api-keys`

Ruft die gespeicherten API-Keys ab (maskiert, nur letzte 4 Zeichen).

**Auth:** Bearer Token erforderlich
**Rate Limit:** 60/min

**Response 200 OK:**
```json
{
  "anthropic": "...XXXX",
  "elevenlabs": "...YYYY",
  "deepgram": null
}
```

**Response Schema:**

| Feld | Typ | Beschreibung |
|---|---|---|
| `anthropic` | `string` \| `null` | Anthropic API Key (maskiert: `...XXXX`) |
| `elevenlabs` | `string` \| `null` | ElevenLabs API Key (maskiert: `...XXXX`) |
| `deepgram` | `string` \| `null` | Deepgram API Key (maskiert: `...XXXX`) |

**Fehlerfaelle:**

| Status | Code | Beschreibung |
|---|---|---|
| 403 | `FORBIDDEN` | Kein oder ungueltiger Access Token |

---

### `PUT /api/v1/settings/api-keys`

Speichert API-Keys (verschluesselt). Nur angegebene Keys werden aktualisiert.

**Auth:** Bearer Token erforderlich
**Rate Limit:** 60/min

**Request Body:**
```json
{
  "anthropic": "sk-ant-api03-xyz...",
  "elevenlabs": "el_key_abc..."
}
```

**Request Schema:**

| Feld | Typ | Pflicht | Validierung | Beschreibung |
|---|---|---|---|---|
| `anthropic` | `string` | Nein | Min. 1 Zeichen | Anthropic API Key (verschluesselt gespeichert) |
| `elevenlabs` | `string` | Nein | Min. 1 Zeichen | ElevenLabs API Key (verschluesselt gespeichert) |
| `deepgram` | `string` | Nein | Min. 1 Zeichen | Deepgram API Key (verschluesselt gespeichert) |

**Response 200 OK:**
```json
{
  "anthropic": "...XXXX",
  "elevenlabs": "...YYYY",
  "deepgram": null
}
```

Gibt maskierte Keys zurueck (gleiche Struktur wie GET).

**Fehlerfaelle:**

| Status | Code | Beschreibung |
|---|---|---|
| 403 | `FORBIDDEN` | Kein oder ungueltiger Access Token |
| 422 | `VALIDATION_ERROR` | Leere Strings oder zu kurze Keys |

**Sicherheit:**
- Keys werden mit Fernet (symmetrische Verschluesselung) gespeichert
- Key-Ableitung via SHA-256 aus `SECRET_KEY`
- Nur maskierte Keys (`...XXXX`) werden zurueckgegeben

---

### `GET /api/v1/settings/voice-providers`

Ruft die aktuellen Voice-Provider-Einstellungen ab.

**Auth:** Bearer Token erforderlich
**Rate Limit:** 60/min

**Response 200 OK:**
```json
{
  "stt_provider": "deepgram",
  "tts_provider": "elevenlabs"
}
```

**Response Schema:**

| Feld | Typ | Beschreibung |
|---|---|---|
| `stt_provider` | `string` | STT Provider (`deepgram`, `whisper`) |
| `tts_provider` | `string` | TTS Provider (`elevenlabs`, `edge-tts`) |

**Fehlerfaelle:**

| Status | Code | Beschreibung |
|---|---|---|
| 403 | `FORBIDDEN` | Kein oder ungueltiger Access Token |

---

### `PUT /api/v1/settings/voice-providers`

Aktualisiert Voice-Provider-Einstellungen.

**Auth:** Bearer Token erforderlich
**Rate Limit:** 60/min

**Request Body:**
```json
{
  "stt_provider": "whisper",
  "tts_provider": "edge-tts"
}
```

**Request Schema:**

| Feld | Typ | Pflicht | Validierung | Beschreibung |
|---|---|---|---|---|
| `stt_provider` | `string` | Nein | `deepgram`, `whisper` | STT Provider |
| `tts_provider` | `string` | Nein | `elevenlabs`, `edge-tts` | TTS Provider |

**Response 200 OK:**
```json
{
  "stt_provider": "whisper",
  "tts_provider": "edge-tts"
}
```

**Fehlerfaelle:**

| Status | Code | Beschreibung |
|---|---|---|
| 403 | `FORBIDDEN` | Kein oder ungueltiger Access Token |
| 422 | `VALIDATION_ERROR` | Ungueltiger Provider-Name |

---

## Memory Endpoints

Memory-Verwaltung fuer das Knowledge Graph & NLP System (Phase 5).

### `GET /api/v1/memory/status`

Gibt den aktuellen Status des Memory-Systems zurueck.

**Auth:** Bearer Token (erforderlich)
**Rate Limit:** 60/min

**Response 200 OK:**
```json
{
  "enabled": true,
  "total_episodes": 42,
  "total_entities": 156,
  "last_analysis_at": "2026-02-14T15:30:00Z"
}
```

**Response Schema:**

| Feld | Typ | Beschreibung |
|---|---|---|
| `enabled` | `boolean` | Memory-System aktiviert? |
| `total_episodes` | `integer` | Anzahl gespeicherter Episoden im Knowledge Graph |
| `total_entities` | `integer` | Anzahl gespeicherter Entitaeten im Knowledge Graph |
| `last_analysis_at` | `string (ISO 8601)` | Zeitpunkt der letzten NLP-Analyse |

**Fehlerfaelle:**

| Status | Code | Beschreibung |
|---|---|---|
| 401 | `UNAUTHORIZED` | Kein oder ungueltiger Access Token |

---

### `GET /api/v1/memory/export`

Exportiert alle gespeicherten Fakten, Relationen und Pattern-Logs (DSGVO Art. 15).

**Auth:** Bearer Token (erforderlich)
**Rate Limit:** 10/min

**Response 200 OK:**
```json
{
  "entities": [],
  "relations": [],
  "pattern_logs": [],
  "exported_at": "2026-02-14T15:30:00Z"
}
```

**Response Schema:**

| Feld | Typ | Beschreibung |
|---|---|---|
| `entities` | `array` | Alle Entitaeten des Users aus dem Knowledge Graph |
| `relations` | `array` | Alle Relationen des Users aus dem Knowledge Graph |
| `pattern_logs` | `array` | Alle NLP-Analyse-Logs aus pattern_logs |
| `exported_at` | `string (ISO 8601)` | Zeitpunkt des Exports |

**Fehlerfaelle:**

| Status | Code | Beschreibung |
|---|---|---|
| 401 | `UNAUTHORIZED` | Kein oder ungueltiger Access Token |

---

### `DELETE /api/v1/memory`

Loescht alle Memory-Daten des Users (Knowledge Graph + pattern_logs). DSGVO Art. 17.

**Auth:** Bearer Token (erforderlich)
**Rate Limit:** 5/min

**Response 200 OK:**
```json
{
  "message": "Alle Memory-Daten wurden geloescht"
}
```

**Fehlerfaelle:**

| Status | Code | Beschreibung |
|---|---|---|
| 401 | `UNAUTHORIZED` | Kein oder ungueltiger Access Token |

---

### `PUT /api/v1/settings/memory`

Schaltet das Memory-System ein oder aus.

**Auth:** Bearer Token (erforderlich)
**Rate Limit:** 60/min

**Request Body:**
```json
{
  "enabled": true
}
```

**Request Schema:**

| Feld | Typ | Pflicht | Beschreibung |
|---|---|---|---|
| `enabled` | `boolean` | Ja | Memory-System ein/ausschalten |

**Response 200 OK:**
```json
{
  "enabled": true
}
```

**Fehlerfaelle:**

| Status | Code | Beschreibung |
|---|---|---|
| 401 | `UNAUTHORIZED` | Kein oder ungueltiger Access Token |
| 422 | `VALIDATION_ERROR` | Ungueltiger Request Body |

---

## Fehlercodes

### Allgemeine HTTP Status Codes

| Status | Bedeutung |
|---|---|
| 200 | OK -- Erfolgreiche Anfrage |
| 201 | Created -- Ressource erfolgreich erstellt |
| 204 | No Content -- Erfolgreich, kein Response Body |
| 400 | Bad Request -- Ungueltige Anfrage |
| 401 | Unauthorized -- Nicht authentifiziert |
| 403 | Forbidden -- Keine Berechtigung |
| 404 | Not Found -- Ressource nicht gefunden |
| 409 | Conflict -- Ressource existiert bereits oder Statuskonflikt |
| 422 | Unprocessable Entity -- Validierungsfehler |
| 429 | Too Many Requests -- Rate Limit ueberschritten |
| 500 | Internal Server Error -- Serverfehler |
| 503 | Service Unavailable -- Service nicht verfuegbar |

### Anwendungsspezifische Fehlercodes

| Code | HTTP Status | Beschreibung | Phase |
|---|---|---|---|
| `EMAIL_ALREADY_EXISTS` | 409 | E-Mail bereits registriert | 1 |
| `INVALID_CREDENTIALS` | 401 | Falsche Login-Daten | 1 |
| `ACCOUNT_DISABLED` | 403 | Account deaktiviert | 1 |
| `UNAUTHORIZED` | 401 | Token fehlt oder ungueltig | 1 |
| `TOKEN_EXPIRED` | 401 | Token abgelaufen | 1 |
| `INVALID_REFRESH_TOKEN` | 401 | Refresh Token ungueltig | 1 |
| `CONVERSATION_NOT_FOUND` | 404 | Konversation nicht gefunden | 1 |
| `VALIDATION_ERROR` | 422 | Eingabevalidierung fehlgeschlagen | 1 |
| `RATE_LIMIT_EXCEEDED` | 429 | Zu viele Anfragen | 1 |
| `AI_SERVICE_UNAVAILABLE` | 503 | KI-Service nicht erreichbar | 1 |
| `INTERNAL_ERROR` | 500 | Interner Serverfehler | 1 |
| `TASK_NOT_FOUND` | 404 | Task nicht gefunden | 2 |
| `TASK_ALREADY_COMPLETED` | 409 | Task ist bereits erledigt | 2 |
| `BRAIN_ENTRY_NOT_FOUND` | 404 | Brain-Eintrag nicht gefunden | 2 |
| `SEARCH_UNAVAILABLE` | 503 | Embedding-Service nicht verfuegbar | 2 |
| `PERSONALITY_PROFILE_NOT_FOUND` | 404 | Persoenlichkeitsprofil nicht gefunden | 2 |
| `PERSONALITY_TEMPLATE_NOT_FOUND` | 404 | Persoenlichkeits-Template nicht gefunden | 2 |
| `ACTIVE_PROFILE_CANNOT_BE_DELETED` | 409 | Aktives Profil kann nicht geloescht werden | 2 |
| `MENTIONED_ITEM_NOT_FOUND` | 404 | Mentioned Item nicht gefunden | 2 |
| `MENTIONED_ITEM_ALREADY_CONVERTED` | 409 | Mentioned Item bereits konvertiert | 2 |

---

## Zusammenfassung

### Phase 1: Foundation

| Method | Path | Beschreibung | Auth | Rate Limit |
|---|---|---|---|---|
| GET | `/health` | Service Health Check | Nein | 60/min |
| POST | `/api/v1/auth/register` | Benutzer-Registrierung | Nein | 5/min |
| POST | `/api/v1/auth/login` | Benutzer-Login | Nein | 5/min |
| POST | `/api/v1/auth/refresh` | Token erneuern | Nein | 10/min |
| POST | `/api/v1/auth/logout` | Ausloggen | Ja | 10/min |
| GET | `/api/v1/auth/me` | Eigenes Profil | Ja | 60/min |
| POST | `/api/v1/chat/message` | Nachricht senden (SSE Streaming) | Ja | 10/min |
| GET | `/api/v1/chat/conversations` | Konversationsliste | Ja | 60/min |
| GET | `/api/v1/chat/conversations/{id}/messages` | Nachrichten einer Konversation | Ja | 60/min |
| WS | `/api/v1/chat/ws` | WebSocket Echtzeit-Chat | Ja (Query) | -- |

### Phase 2: Core Features

| Method | Path | Beschreibung | Auth | Rate Limit |
|---|---|---|---|---|
| POST | `/api/v1/tasks` | Task erstellen | Ja | 60/min |
| GET | `/api/v1/tasks` | Tasks auflisten (paginiert, gefiltert) | Ja | 60/min |
| GET | `/api/v1/tasks/today` | Heutige Tasks | Ja | 60/min |
| GET | `/api/v1/tasks/{id}` | Task abrufen (inkl. Sub-Tasks) | Ja | 60/min |
| PUT | `/api/v1/tasks/{id}` | Task aktualisieren (Partial Update) | Ja | 60/min |
| DELETE | `/api/v1/tasks/{id}` | Task loeschen (CASCADE Sub-Tasks) | Ja | 60/min |
| POST | `/api/v1/tasks/{id}/complete` | Task erledigen (+XP, Level, Streak) | Ja | 60/min |
| POST | `/api/v1/brain/entries` | Brain-Eintrag erstellen | Ja | 60/min |
| GET | `/api/v1/brain/entries` | Eintraege auflisten (paginiert, gefiltert) | Ja | 60/min |
| GET | `/api/v1/brain/entries/{id}` | Eintrag abrufen | Ja | 60/min |
| PUT | `/api/v1/brain/entries/{id}` | Eintrag aktualisieren (Re-Embedding bei Content-Aenderung) | Ja | 60/min |
| DELETE | `/api/v1/brain/entries/{id}` | Eintrag loeschen (CASCADE Embeddings) | Ja | 60/min |
| GET | `/api/v1/brain/search` | Semantische Suche (pgvector Cosine Similarity) | Ja | 60/min |
| POST | `/api/v1/personality/profiles` | Profil erstellen (optional aus Template) | Ja | 60/min |
| GET | `/api/v1/personality/profiles` | Profile auflisten | Ja | 60/min |
| PUT | `/api/v1/personality/profiles/{id}` | Profil bearbeiten | Ja | 60/min |
| DELETE | `/api/v1/personality/profiles/{id}` | Profil loeschen | Ja | 60/min |
| POST | `/api/v1/personality/profiles/{id}/activate` | Profil aktivieren | Ja | 60/min |
| GET | `/api/v1/personality/templates` | Templates auflisten | Ja | 60/min |
| GET | `/api/v1/personality/preview` | Personality Preview (AI-generiert) | Ja | 10/min |
| GET | `/api/v1/proactive/mentioned-items` | Mentioned Items auflisten | Ja | 60/min |
| POST | `/api/v1/proactive/mentioned-items/{id}/convert` | Item zu Task/Brain-Eintrag konvertieren | Ja | 60/min |
| POST | `/api/v1/proactive/mentioned-items/{id}/dismiss` | Item verwerfen | Ja | 60/min |
| POST | `/api/v1/proactive/mentioned-items/{id}/snooze` | Item snoozen | Ja | 60/min |

### Phase 3: ADHS-Modus Settings & Voice

| Method | Path | Beschreibung | Auth | Rate Limit |
|---|---|---|---|---|
| GET | `/api/v1/settings/adhs` | ADHS-Einstellungen abrufen | Ja | 60/min |
| PUT | `/api/v1/settings/adhs` | ADHS-Einstellungen aktualisieren | Ja | 60/min |
| POST | `/api/v1/settings/push-token` | Expo Push Token registrieren | Ja | 60/min |
| POST | `/api/v1/settings/onboarding` | Onboarding abschliessen | Ja | 60/min |
| GET | `/api/v1/settings/api-keys` | API-Keys abrufen (maskiert) | Ja | 60/min |
| PUT | `/api/v1/settings/api-keys` | API-Keys speichern (verschluesselt) | Ja | 60/min |
| GET | `/api/v1/settings/voice-providers` | Voice-Provider-Einstellungen abrufen | Ja | 60/min |
| PUT | `/api/v1/settings/voice-providers` | Voice-Provider-Einstellungen aktualisieren | Ja | 60/min |

### Phase 5: Memory

| Method | Path | Beschreibung | Auth | Rate Limit |
|---|---|---|---|---|
| GET | `/api/v1/memory/status` | Memory-System Status | Ja | 60/min |
| GET | `/api/v1/memory/export` | DSGVO Art. 15 Datenexport | Ja | 10/min |
| DELETE | `/api/v1/memory` | DSGVO Art. 17 Komplett-Loeschung | Ja | 5/min |
| PUT | `/api/v1/settings/memory` | Memory ein/ausschalten | Ja | 60/min |

**Gesamt: 40 Endpoints** (Phase 1: 10, Phase 2: 14, Phase 3: 12, Phase 5: 4)

---

## Geplante Endpoints (Phase 4+)

> Diese Endpoints werden spezifiziert, wenn die jeweilige Phase implementiert wird.

### Phase 4: Plugins & Extras

| Method | Path | Beschreibung |
|---|---|---|
| GET | `/api/v1/plugins` | Verfuegbare Plugins auflisten |
| POST | `/api/v1/plugins/{id}/install` | Plugin installieren |
| POST | `/api/v1/plugins/{id}/uninstall` | Plugin deinstallieren |
| GET | `/api/v1/plugins/{id}/settings` | Plugin-Einstellungen lesen |
| PUT | `/api/v1/plugins/{id}/settings` | Plugin-Einstellungen aendern |
| POST | `/api/v1/plugins/{id}/auth` | Plugin OAuth starten |
| POST | `/api/v1/plugins/{id}/webhook` | Plugin Webhook empfangen |
| GET | `/api/v1/calendar/events` | Kalender-Events abrufen |
| POST | `/api/v1/calendar/sync` | Kalender-Sync starten |
