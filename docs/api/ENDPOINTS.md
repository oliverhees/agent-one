# API Endpoints

**Version:** 1.0
**Datum:** 2026-02-06
**Base URL:** `https://api.alice-app.de/api/v1`
**Dokumentation:** Auto-generiert via FastAPI (Swagger UI unter `/docs`, ReDoc unter `/redoc`)

---

## Inhaltsverzeichnis

1. [Allgemeine Konventionen](#allgemeine-konventionen)
2. [Health Check](#health-check)
3. [Auth Endpoints](#auth-endpoints)
4. [Chat Endpoints](#chat-endpoints)
5. [Fehlercodes](#fehlercodes)

> **Hinweis:** Dieses Dokument spezifiziert die Endpoints fuer **Phase 1 (Foundation)**. Spaetere Phasen werden ergaenzt, wenn die Implementierung ansteht.

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
| 409 | Conflict -- Ressource existiert bereits |
| 422 | Unprocessable Entity -- Validierungsfehler |
| 429 | Too Many Requests -- Rate Limit ueberschritten |
| 500 | Internal Server Error -- Serverfehler |
| 503 | Service Unavailable -- Service nicht verfuegbar |

### Anwendungsspezifische Fehlercodes

| Code | HTTP Status | Beschreibung |
|---|---|---|
| `EMAIL_ALREADY_EXISTS` | 409 | E-Mail bereits registriert |
| `INVALID_CREDENTIALS` | 401 | Falsche Login-Daten |
| `ACCOUNT_DISABLED` | 403 | Account deaktiviert |
| `UNAUTHORIZED` | 401 | Token fehlt oder ungueltig |
| `TOKEN_EXPIRED` | 401 | Token abgelaufen |
| `INVALID_REFRESH_TOKEN` | 401 | Refresh Token ungueltig |
| `CONVERSATION_NOT_FOUND` | 404 | Konversation nicht gefunden |
| `VALIDATION_ERROR` | 422 | Eingabevalidierung fehlgeschlagen |
| `RATE_LIMIT_EXCEEDED` | 429 | Zu viele Anfragen |
| `AI_SERVICE_UNAVAILABLE` | 503 | KI-Service nicht erreichbar |
| `INTERNAL_ERROR` | 500 | Interner Serverfehler |

---

## Zusammenfassung Phase 1

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

---

## Geplante Endpoints (Phase 2-4)

> Diese Endpoints werden spezifiziert, wenn die jeweilige Phase implementiert wird.

### Phase 2: Core Features

| Method | Path | Beschreibung |
|---|---|---|
| POST | `/api/v1/tasks` | Task erstellen |
| GET | `/api/v1/tasks` | Tasks auflisten |
| GET | `/api/v1/tasks/{id}` | Task abrufen |
| PUT | `/api/v1/tasks/{id}` | Task aktualisieren |
| DELETE | `/api/v1/tasks/{id}` | Task loeschen |
| POST | `/api/v1/tasks/{id}/complete` | Task erledigen (+XP) |
| POST | `/api/v1/tasks/{id}/breakdown` | Task aufteilen (AI) |
| GET | `/api/v1/tasks/today` | Heutige Tasks |
| POST | `/api/v1/brain/entries` | Brain-Eintrag erstellen |
| GET | `/api/v1/brain/entries` | Eintraege auflisten |
| GET | `/api/v1/brain/entries/{id}` | Eintrag abrufen |
| PUT | `/api/v1/brain/entries/{id}` | Eintrag aktualisieren |
| DELETE | `/api/v1/brain/entries/{id}` | Eintrag loeschen |
| GET | `/api/v1/brain/search` | Semantische Suche |
| POST | `/api/v1/brain/ingest` | URL/Datei importieren |
| GET | `/api/v1/proactive/mentioned-items` | Mentioned Items auflisten |
| POST | `/api/v1/proactive/mentioned-items/{id}/convert` | Item konvertieren |
| POST | `/api/v1/proactive/mentioned-items/{id}/dismiss` | Item verwerfen |
| GET | `/api/v1/proactive/daily-plan` | Tagesplan abrufen |
| GET | `/api/v1/proactive/settings` | Proaktive Einstellungen lesen |
| PUT | `/api/v1/proactive/settings` | Proaktive Einstellungen aendern |
| POST | `/api/v1/proactive/snooze` | Notifications snoozen |
| POST | `/api/v1/personality/profiles` | Profil erstellen |
| GET | `/api/v1/personality/profiles` | Profile auflisten |
| PUT | `/api/v1/personality/profiles/{id}` | Profil bearbeiten |
| DELETE | `/api/v1/personality/profiles/{id}` | Profil loeschen |
| POST | `/api/v1/personality/profiles/{id}/activate` | Profil aktivieren |
| GET | `/api/v1/personality/traits` | Traits lesen |
| PUT | `/api/v1/personality/traits` | Traits aendern |
| GET | `/api/v1/personality/rules` | Rules lesen |
| POST | `/api/v1/personality/rules` | Rule hinzufuegen |
| DELETE | `/api/v1/personality/rules/{id}` | Rule loeschen |
| GET | `/api/v1/personality/templates` | Templates auflisten |
| GET | `/api/v1/personality/preview` | Personality Preview |

### Phase 3: ADHS-Modus

| Method | Path | Beschreibung |
|---|---|---|
| GET | `/api/v1/gamification/stats` | XP, Level, Streak |
| GET | `/api/v1/gamification/history` | XP-Verlauf |
| GET | `/api/v1/gamification/achievements` | Achievements auflisten |

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
| GET | `/api/v1/personality/voice` | Voice-Einstellungen lesen |
| PUT | `/api/v1/personality/voice` | Voice-Einstellungen aendern |
