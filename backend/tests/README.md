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

## WICHTIGER HINWEIS

**CRITICAL BUG:** Die Models verwenden PostgreSQL-spezifische Typen (`PG_UUID`, `JSONB`), die **NICHT mit SQLite kompatibel** sind.

Die Tests werden aktuell **NICHT** laufen können, weil:
1. `conftest.py` verwendet SQLite in-memory DB: `sqlite+aiosqlite:///:memory:`
2. Models verwenden `sqlalchemy.dialects.postgresql.UUID` und `JSONB`
3. SQLite unterstützt diese Typen nicht

### Lösung 1: PostgreSQL Testcontainer (EMPFOHLEN)

Verwende `testcontainers` um eine echte PostgreSQL-Instanz für Tests zu starten:

```bash
pip install testcontainers[postgres]
```

Dann in `conftest.py`:
```python
from testcontainers.postgres import PostgresContainer

@pytest.fixture(scope="session")
def postgres_container():
    with PostgresContainer("postgres:16-alpine") as postgres:
        yield postgres

@pytest.fixture
async def test_db(postgres_container):
    engine = create_async_engine(postgres_container.get_connection_url())
    # ... rest of the code
```

### Lösung 2: Models SQLite-kompatibel machen

In `app/models/base.py` und allen anderen Models:
```python
from sqlalchemy import String
from sqlalchemy.dialects import postgresql
from uuid import UUID as PyUUID

# Conditional UUID type
UUID_TYPE = postgresql.UUID(as_uuid=True) if dialect == "postgresql" else String(36)
```

### Lösung 3: Nur PostgreSQL für Tests verwenden

`.env.test`:
```env
DATABASE_URL=postgresql+asyncpg://test:test@localhost:5432/alice_test
```

Und vor Tests:
```bash
docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=test -e POSTGRES_USER=test -e POSTGRES_DB=alice_test postgres:16-alpine
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
