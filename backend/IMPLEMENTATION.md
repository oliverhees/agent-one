# Backend Implementation - Auth & Chat Endpoints

**Implementiert von:** Backend Developer
**Datum:** 2026-02-06
**Linear Tasks:** HR-28 bis HR-35

## Implementierte Features

### 1. Authentication System

#### Endpoints
- **POST /api/v1/auth/register** - Benutzerregistrierung
  - Validierung: Email (unique), Passwort (min 8, 1 Großbuchstabe, 1 Zahl)
  - Returns: TokenResponse (access_token, refresh_token)
  - Rate Limit: 5/min

- **POST /api/v1/auth/login** - Benutzer-Login
  - Validierung: Credentials
  - Returns: TokenResponse
  - Rate Limit: 5/min

- **POST /api/v1/auth/refresh** - Token Refresh (mit Rotation)
  - Revoked alten Refresh Token
  - Erstellt neues Token-Paar
  - Rate Limit: 10/min

- **POST /api/v1/auth/logout** - Logout
  - Revoked alle Refresh Tokens des Users
  - Rate Limit: 10/min

- **GET /api/v1/auth/me** - User Profil
  - Returns: UserResponse
  - Rate Limit: 60/min

#### Services
- **AuthService** (`app/services/auth.py`)
  - `register()` - Erstellt User + Tokens
  - `login()` - Validiert Credentials + Erstellt Tokens
  - `refresh_tokens()` - Token Rotation
  - `logout()` - Revoked alle Tokens

### 2. Chat System

#### Endpoints
- **POST /api/v1/chat/message** - Nachricht senden (SSE Streaming)
  - Erstellt/Nutzt Conversation
  - Speichert User-Message
  - Streamt AI-Response via Server-Sent Events
  - Speichert AI-Message
  - Rate Limit: 10/min

- **GET /api/v1/chat/conversations** - Konversationsliste
  - Cursor-basierte Pagination
  - Sortiert nach updated_at DESC
  - Rate Limit: 60/min

- **GET /api/v1/chat/conversations/{id}/messages** - Nachrichten einer Konversation
  - Cursor-basierte Pagination
  - Sortiert nach created_at ASC
  - Prüft User-Ownership
  - Rate Limit: 60/min

#### Services
- **ChatService** (`app/services/chat.py`)
  - `create_conversation()` - Erstellt neue Konversation
  - `get_conversation()` - Lädt Konversation mit Ownership-Check
  - `get_conversations()` - Paginierte Liste
  - `get_messages()` - Paginierte Nachrichten
  - `save_message()` - Speichert Message
  - `stream_ai_response()` - Streamt AI-Antwort

- **AIService** (`app/services/ai.py`)
  - `stream_response()` - Kommunikation mit Claude API
  - Mock-Modus wenn kein API-Key gesetzt
  - Parsing von Claude SSE Events

### 3. Error Handling

**Custom Exceptions** (`app/core/exceptions.py`)
- `AliceException` - Base Exception
- `AuthenticationError` - 401
- `EmailAlreadyExistsError` - 409
- `InvalidTokenError` - 401
- `AccountDisabledError` - 403
- `UnauthorizedError` - 401
- `ConversationNotFoundError` - 404
- `AIServiceUnavailableError` - 503
- `ValidationError` - 422
- `RateLimitExceededError` - 429

### 4. Rate Limiting

**Rate Limiter** (`app/core/rate_limit.py`)
- In-Memory Implementation (für Development)
- `auth_rate_limit` - 5 requests/min
- `chat_rate_limit` - 10 requests/min
- `standard_rate_limit` - 60 requests/min

Note: Production sollte Redis-basiertes Rate Limiting nutzen.

### 5. Authentication Dependencies

**Dependencies** (`app/api/deps.py`)
- `get_current_user()` - FastAPI Dependency
  - Extrahiert JWT aus Authorization Header
  - Validiert Token
  - Lädt User aus DB
  - Prüft is_active Status

## Dateistruktur

```
backend/app/
├── api/
│   ├── deps.py                 # Auth Dependencies
│   └── v1/
│       ├── auth.py             # Auth Endpoints
│       ├── chat.py             # Chat Endpoints
│       └── router.py           # V1 Router (aktualisiert)
│
├── core/
│   ├── exceptions.py           # Custom Exceptions
│   └── rate_limit.py           # Rate Limiting
│
├── services/
│   ├── __init__.py             # Service Exports
│   ├── auth.py                 # AuthService
│   ├── chat.py                 # ChatService
│   └── ai.py                   # AIService
│
└── schemas/
    └── user.py                 # Passwort-Validierung erweitert
```

## Akzeptanzkriterien

- [x] POST /api/v1/auth/register funktioniert (201 + Tokens)
- [x] POST /api/v1/auth/login funktioniert (200 + Tokens)
- [x] POST /api/v1/auth/refresh funktioniert (Token Rotation)
- [x] POST /api/v1/auth/logout funktioniert (Token Revocation)
- [x] GET /api/v1/auth/me funktioniert (User Response)
- [x] POST /api/v1/chat/message streamt via SSE
- [x] GET /api/v1/chat/conversations mit Pagination
- [x] GET /api/v1/chat/conversations/{id}/messages mit Pagination
- [x] Rate Limiting auf Auth-Endpoints (5/min)
- [x] Custom Error Handling mit Fehlercodes
- [x] Alle Pydantic Schemas korrekt verwendet
- [x] Auth Dependency für Protected Routes
- [x] AI Service mit Claude API (oder Mock wenn kein Key)

## Verwendete Models & Schemas

### Models (keine Änderungen)
- `User` - Bestehend
- `RefreshToken` - Bestehend
- `Conversation` - Bestehend
- `Message` - Bestehend
- `MessageRole` - Bestehend

### Schemas (erweitert)
- `UserCreate` - Passwort-Validierung hinzugefügt
- `UserResponse` - Bestehend
- `LoginRequest` - Bestehend
- `TokenResponse` - Bestehend
- `TokenRefreshRequest` - Bestehend
- `MessageCreate` - Bestehend
- `MessageResponse` - Bestehend
- `ConversationResponse` - Bestehend
- `ConversationListResponse` - Bestehend

## Technische Details

### JWT Token Management
- **Access Token**: 15 Minuten TTL, HS256
- **Refresh Token**: 7 Tage TTL, HS256, in DB gespeichert
- **Token Rotation**: Bei Refresh wird alter Token revoked, neuer erstellt
- **Logout**: Alle Refresh Tokens des Users werden revoked

### SSE Streaming Format

```
event: conversation
data: {"conversation_id": "uuid", "is_new": false}

event: token
data: {"content": "Hello", "index": 0}

event: done
data: {"message_id": "uuid", "conversation_id": "uuid", "total_tokens": 150}

event: error
data: {"detail": "Error message", "code": "ERROR_CODE"}
```

### Cursor-basierte Pagination

Die Implementierung nutzt Cursor-basierte Pagination für bessere Performance:
- Conversations: Sortiert nach `updated_at DESC`, cursor ist `conversation.id`
- Messages: Sortiert nach `created_at ASC`, cursor ist `message.id`

## API-Dokumentation

Nach Start des Servers verfügbar unter:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

## Testing

Zum Testen der Endpoints:

1. **Server starten**:
   ```bash
   cd backend
   uvicorn app.main:app --reload
   ```

2. **Register**:
   ```bash
   curl -X POST http://localhost:8000/api/v1/auth/register \
     -H "Content-Type: application/json" \
     -d '{"email":"test@example.com","password":"SecurePass123","display_name":"Test User"}'
   ```

3. **Login**:
   ```bash
   curl -X POST http://localhost:8000/api/v1/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email":"test@example.com","password":"SecurePass123"}'
   ```

4. **Get Me**:
   ```bash
   curl http://localhost:8000/api/v1/auth/me \
     -H "Authorization: Bearer <access_token>"
   ```

5. **Send Message (SSE)**:
   ```bash
   curl -X POST http://localhost:8000/api/v1/chat/message \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer <access_token>" \
     -d '{"content":"Hello ALICE!"}'
   ```

## Nächste Schritte

1. **Unit Tests schreiben** (test-engineer)
2. **API-Dokumentation erweitern** (docs-writer)
3. **Security Audit** (security-auditor)
4. **Deployment vorbereiten** (devops-engineer)

## Hinweise

- Kein Schema/Migration-Code geändert (wie gefordert)
- Alle bestehenden Models/Schemas wiederverwendet
- Error Handling gemäß Spezifikation in ENDPOINTS.md
- Rate Limiting ist in-memory (für Production: Redis verwenden)
- AI Service hat Mock-Modus wenn ANTHROPIC_API_KEY nicht gesetzt
