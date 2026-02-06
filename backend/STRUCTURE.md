# Backend Structure Documentation

Complete overview of the ALICE backend architecture and file organization.

## Directory Tree

```
backend/
├── app/
│   ├── __init__.py                  # Package init with version
│   ├── main.py                      # FastAPI app entry point
│   │
│   ├── core/                        # Core functionality
│   │   ├── __init__.py
│   │   ├── config.py                # Pydantic Settings (env vars)
│   │   ├── database.py              # SQLAlchemy async setup
│   │   └── security.py              # JWT + password hashing
│   │
│   ├── api/                         # API routes
│   │   ├── __init__.py
│   │   └── v1/                      # API version 1
│   │       ├── __init__.py
│   │       ├── router.py            # Main v1 router
│   │       └── health.py            # Health check endpoint
│   │
│   ├── models/                      # SQLAlchemy models
│   │   ├── __init__.py
│   │   └── base.py                  # Base model with id, timestamps
│   │
│   ├── schemas/                     # Pydantic schemas
│   │   └── __init__.py
│   │
│   └── services/                    # Business logic
│       └── __init__.py
│
├── alembic/                         # Database migrations
│   ├── env.py                       # Alembic async config
│   ├── script.py.mako               # Migration template
│   └── versions/                    # Migration files
│
├── tests/                           # Tests
│   ├── __init__.py
│   └── conftest.py                  # Pytest fixtures
│
├── requirements.txt                 # Production dependencies
├── requirements-dev.txt             # Development dependencies
├── pyproject.toml                   # Python project config
├── alembic.ini                      # Alembic configuration
├── Dockerfile                       # Multi-stage Docker build
├── .dockerignore                    # Docker ignore patterns
└── README.md                        # Backend documentation
```

## Core Modules

### app/main.py

**Purpose**: FastAPI application entry point

**Key Features**:
- Lifespan context manager for startup/shutdown
- CORS middleware configuration
- API v1 router inclusion
- OpenAPI documentation at `/docs`

**Startup Flow**:
1. Load settings from environment
2. Initialize database connection
3. Configure CORS
4. Mount API routes
5. Start uvicorn server

### app/core/config.py

**Purpose**: Centralized configuration using Pydantic Settings

**Key Classes**:
- `Settings`: Loads all env vars with validation
- Properties for computed values (database URLs)

**Environment Variables**:
- App: `APP_NAME`, `APP_ENV`, `DEBUG`, `SECRET_KEY`
- Database: `POSTGRES_*`, `DATABASE_URL`
- Redis: `REDIS_HOST`, `REDIS_PORT`, `REDIS_URL`
- JWT: `JWT_SECRET_KEY`, `JWT_*_EXPIRE_*`
- AI: `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`
- CORS: `CORS_ORIGINS` (JSON array or comma-separated)

### app/core/database.py

**Purpose**: SQLAlchemy async database setup

**Key Components**:
- `engine`: Async database engine
- `AsyncSessionLocal`: Session factory
- `get_db()`: FastAPI dependency for DB sessions
- `init_db()`: Initialize DB on startup
- `close_db()`: Close DB on shutdown

**Usage Example**:
```python
from app.core.database import get_db

@router.get("/users")
async def get_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User))
    return result.scalars().all()
```

### app/core/security.py

**Purpose**: Authentication and security utilities

**Functions**:
- `hash_password(password)`: Hash password with bcrypt
- `verify_password(plain, hashed)`: Verify password
- `create_access_token(data)`: Create JWT access token
- `create_refresh_token(data)`: Create JWT refresh token
- `verify_token(token, type)`: Verify and decode JWT
- `get_current_user()`: FastAPI dependency for auth

**Usage Example**:
```python
from app.core.security import get_current_user

@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    return {"user_id": current_user["sub"]}
```

### app/models/base.py

**Purpose**: Base SQLAlchemy model with common fields

**Base Classes**:
- `Base`: SQLAlchemy declarative base
- `BaseModel`: Abstract model with id, created_at, updated_at

**Usage Example**:
```python
from app.models.base import BaseModel

class User(BaseModel):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(unique=True)
    name: Mapped[str]
```

### app/api/v1/health.py

**Purpose**: Health check endpoint

**Endpoint**: `GET /api/v1/health`

**Checks**:
- Database connection (PostgreSQL)
- Redis connection
- Overall status

**Response**:
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "services": {
    "db": "ok",
    "redis": "ok"
  }
}
```

## Database Migrations (Alembic)

### Configuration

**alembic.ini**: Main Alembic configuration
- Script location: `alembic/`
- Database URL: From `app.core.config.settings`

**alembic/env.py**: Migration environment
- Async support enabled
- Auto-imports models from `app.models.base.Base`
- Uses sync database URL for migrations

### Commands

**Create migration**:
```bash
alembic revision --autogenerate -m "description"
```

**Apply migrations**:
```bash
alembic upgrade head
```

**Rollback**:
```bash
alembic downgrade -1
```

**View history**:
```bash
alembic history
```

## Docker Setup

### Dockerfile

**Multi-stage build**:
1. **Builder stage**: Compile dependencies
2. **Runtime stage**: Minimal production image

**Features**:
- Python 3.12-slim base
- Non-root user (appuser, UID 1000)
- Health check endpoint
- Optimized layer caching

**Image size**: ~300MB

### docker-compose.yml

**Services**:
- `api`: FastAPI backend (port 8000)
- `db`: PostgreSQL 16 + pgvector (port 5432)
- `redis`: Redis 7 (port 6379)

**Volumes**:
- `postgres_data`: Database persistence
- `redis_data`: Redis persistence

**Networks**:
- `alice-network`: Bridge network for inter-service communication

### docker-compose.dev.yml

**Development overrides**:
- Hot reload enabled (`--reload`)
- Volume mount for code changes
- Debug mode enabled
- Separate dev database

## Dependencies

### Production (requirements.txt)

| Package | Purpose |
|---------|---------|
| fastapi | Web framework |
| uvicorn | ASGI server |
| sqlalchemy | Async ORM |
| asyncpg | PostgreSQL driver |
| alembic | Migrations |
| pydantic | Validation |
| python-jose | JWT |
| passlib | Password hashing |
| redis | Caching |
| celery | Background tasks |
| httpx | HTTP client |
| python-multipart | File uploads |

### Development (requirements-dev.txt)

| Package | Purpose |
|---------|---------|
| pytest | Testing framework |
| pytest-asyncio | Async test support |
| pytest-cov | Coverage |
| ruff | Linting + formatting |
| mypy | Type checking |

## Code Quality

### Ruff Configuration (pyproject.toml)

- Line length: 100
- Target: Python 3.12
- Enabled rules: pycodestyle, pyflakes, isort, flake8-bugbear
- Ignored: E501 (line length), B008, C901

### MyPy Configuration (pyproject.toml)

- Strict mode enabled
- Disallow untyped definitions
- Check untyped definitions
- Warn on unused configs

### Pytest Configuration (pyproject.toml)

- Test path: `tests/`
- Async mode: auto
- Coverage: 80% minimum
- Reports: terminal, HTML, XML

## API Structure

### Versioning

- Base path: `/api/v1`
- Health check: `/api/v1/health`
- Future: `/api/v2` for breaking changes

### Endpoints Pattern

```
/api/v1/
├── /health              # Health check
├── /auth/
│   ├── /login           # JWT login
│   ├── /refresh         # Refresh token
│   └── /logout          # Logout
├── /users/
│   ├── /me              # Current user
│   ├── /{id}            # User by ID
│   └── /                # List users
├── /tasks/              # Task management
├── /goals/              # Goal tracking
└── /insights/           # AI insights
```

### Response Format

**Success**:
```json
{
  "data": { ... },
  "message": "Success",
  "timestamp": "2026-02-06T20:00:00Z"
}
```

**Error**:
```json
{
  "detail": "Error message",
  "status_code": 400
}
```

## Security

### Authentication Flow

1. User submits credentials to `/auth/login`
2. Backend verifies credentials
3. Backend creates access token (15 min) + refresh token (7 days)
4. Client stores tokens
5. Client includes access token in `Authorization: Bearer <token>`
6. Backend verifies token via `get_current_user()` dependency
7. Client refreshes access token via `/auth/refresh`

### Password Security

- Hashing: bcrypt (automatically salted)
- Rounds: 12 (default)
- No plain passwords stored

### JWT Security

- Algorithm: HS256
- Access token: 15 minutes expiry
- Refresh token: 7 days expiry
- Token type included in payload

### CORS Security

- Configured origins only (no wildcard in production)
- Credentials allowed
- All methods allowed (restrict in production if needed)

## Testing

### Test Structure

```
tests/
├── conftest.py          # Fixtures
├── test_health.py       # Health check tests
├── test_auth.py         # Authentication tests
└── test_models.py       # Model tests
```

### Fixtures (conftest.py)

- `test_db`: In-memory SQLite for fast tests
- `client`: Async test client
- `event_loop`: Event loop for async tests

### Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=app --cov-report=html

# Specific test
pytest tests/test_health.py

# With output
pytest -v -s
```

## Development Workflow

### 1. Create Feature Branch

```bash
git checkout -b feature/user-auth
```

### 2. Implement Feature

- Add models in `app/models/`
- Add schemas in `app/schemas/`
- Add routes in `app/api/v1/`
- Add business logic in `app/services/`

### 3. Create Migration

```bash
alembic revision --autogenerate -m "add users table"
```

### 4. Write Tests

- Unit tests for services
- Integration tests for routes
- E2E tests for workflows

### 5. Run Quality Checks

```bash
ruff check . --fix
ruff format .
mypy app/
pytest --cov=app
```

### 6. Commit

```bash
git add .
git commit -m "[LINEAR-ID] feat(auth): implement user authentication"
```

## Production Checklist

Before deploying to production:

- [ ] All tests passing
- [ ] Code linting clean
- [ ] Type checking clean
- [ ] Coverage >= 80%
- [ ] Environment variables set
- [ ] Secrets changed from defaults
- [ ] Database migrations applied
- [ ] Health check responding
- [ ] CORS origins configured
- [ ] SSL/HTTPS enabled
- [ ] Backups configured
- [ ] Monitoring configured
- [ ] Documentation updated

## Performance Tips

### Database

- Use indexes on frequently queried columns
- Use `select(User).options(selectinload(User.tasks))` for eager loading
- Use `db.execute()` with compiled statements
- Enable connection pooling

### Redis

- Use for session storage
- Cache expensive queries
- Set appropriate TTLs
- Use Redis for Celery broker

### API

- Use background tasks for slow operations
- Paginate list endpoints
- Use ETags for caching
- Compress responses

### Monitoring

- Log all errors with context
- Track response times
- Monitor database connections
- Monitor memory usage

---

**Maintained by**: DevOps Engineer
**Last Updated**: 2026-02-06
**Version**: 0.1.0
