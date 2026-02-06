# Backend Tests - ALICE

## Test-Struktur

```
tests/
├── conftest.py              # Pytest fixtures (DB, Client, Auth)
├── test_auth.py             # Auth endpoint tests (15+ tests)
├── test_chat.py             # Chat endpoint tests (8+ tests)
├── test_security.py         # Security unit tests (8+ tests)
├── BUG_REPORT.md            # Gefundene Bugs
└── README.md                # Diese Datei
```

## Voraussetzungen

Die Tests verwenden eine **PostgreSQL Test-Datenbank** statt SQLite, da die Models PostgreSQL-spezifische Typen verwenden (`UUID`, `JSONB`, `pgvector`).

### 1. PostgreSQL starten

```bash
docker compose up -d db
```

### 2. Test-Datenbank erstellen

**Option A: Automatisches Setup (empfohlen)**
```bash
./scripts/setup-test-db.sh
```

**Option B: Manuell**
```bash
docker compose exec db psql -U alice -c "CREATE DATABASE alice_test;"
docker compose exec db psql -U alice -d alice_test -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

### 3. Dependencies installieren

```bash
pip install -r requirements-dev.txt
```

## Tests ausführen

### Alle Tests
```bash
pytest
```

### Mit Coverage Report
```bash
pytest --cov=app --cov-report=term-missing
```

### Nur Auth Tests
```bash
pytest tests/test_auth.py
```

### Nur Chat Tests
```bash
pytest tests/test_chat.py
```

### Nur Security Unit Tests
```bash
pytest tests/test_security.py
```

### Verbose Output
```bash
pytest -v
```

### Mit Print Statements
```bash
pytest -s
```

## Test-Datenbank Details

**Connection String:**
```
postgresql+asyncpg://alice:alice_dev_123@localhost:5432/alice_test
```

**Eigenschaften:**
- Separate Datenbank nur für Tests
- Tabellen werden einmalig pro Test-Session erstellt
- Jeder Test läuft in einer eigenen Transaktion (automatisches Rollback)
- Keine gegenseitige Beeinflussung zwischen Tests
- pgvector Extension aktiviert für Vector-Embeddings

## Test-Datenbank zurücksetzen

Falls die Test-DB in einen inkonsistenten Zustand gerät:

```bash
./scripts/setup-test-db.sh
```

Oder manuell:
```bash
docker compose exec db psql -U alice -c "DROP DATABASE IF EXISTS alice_test;"
docker compose exec db psql -U alice -c "CREATE DATABASE alice_test;"
docker compose exec db psql -U alice -d alice_test -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

## Test Coverage Ziel

- **Unit Tests:** >= 80% Coverage
- **E2E/Integration:** Alle kritischen User Flows

## Aktueller Stand

### Auth Tests (test_auth.py)
- [x] Register Success (201)
- [x] Register Duplicate Email (409)
- [x] Register Invalid Email (422)
- [x] Register Weak Password - Too Short (422)
- [x] Register Weak Password - No Uppercase (422)
- [x] Register Weak Password - No Number (422)
- [x] Register Missing Fields (422)
- [x] Login Success (200)
- [x] Login Wrong Password (401)
- [x] Login Nonexistent Email (401)
- [x] Login Missing Fields (422)
- [x] Refresh Success (200)
- [x] Refresh Invalid Token (401)
- [x] Refresh Expired Token (401)
- [x] Refresh Revoked Token (401)
- [x] Logout Success (200)
- [x] Logout Unauthenticated (401)
- [x] Logout Invalid Token (401)
- [x] Me Success (200)
- [x] Me Unauthenticated (401)
- [x] Me Invalid Token (401)

**Total: 21 Tests**

### Chat Tests (test_chat.py)
- [x] Send Message Creates Conversation (SSE Stream)
- [x] Send Message Existing Conversation (SSE Stream)
- [x] Send Message Unauthenticated (401)
- [x] Get Conversations Empty (200)
- [x] Get Conversations With Data (200)
- [x] Get Conversations Pagination (Cursor-based)
- [x] Get Conversations Unauthenticated (401)
- [x] Get Messages Success (200)
- [x] Get Messages Wrong Conversation (404)
- [x] Get Messages Nonexistent Conversation (404)
- [x] Get Messages Unauthenticated (401)

**Total: 11 Tests**

### Security Tests (test_security.py)
- [x] Hash Password
- [x] Hash Password Different Each Time (Salt)
- [x] Verify Password Correct
- [x] Verify Password Wrong
- [x] Verify Password Empty
- [x] Create Access Token
- [x] Create Refresh Token
- [x] Verify Token Valid Access
- [x] Verify Token Valid Refresh
- [x] Verify Token Wrong Type
- [x] Verify Token Expired
- [x] Verify Token Invalid Signature
- [x] Verify Token Malformed
- [x] Token With Additional Claims
- [x] Empty Token String

**Total: 15 Tests**

## Grand Total: 47 Tests

## Fehlende Tests (siehe BUG_REPORT.md)

1. **Rate Limiting Tests** - Prüfen ob Rate Limits greifen (429)
2. **SSE Stream Error Handling** - Error events bei Stream-Fehlern
3. **Account Disabled** - Login/Me mit deaktiviertem Account
4. **Conversation Access Control** - User B kann User A's Conversations nicht sehen
5. **Message Pagination** - Cursor-based Pagination für Messages
6. **Token Blacklist** - Access Token sollte nach Logout ungültig sein (aktuell nur Refresh Tokens)

## Dependencies

Alle nötigen Dependencies sind in `requirements-dev.txt`:
- pytest
- pytest-asyncio
- pytest-cov
- httpx
- aiosqlite

Install mit:
```bash
pip install -r requirements-dev.txt
```
