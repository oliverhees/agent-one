# ALICE Backend

FastAPI backend for ALICE - Proactive Personal Assistant with ADHD Focus.

## Tech Stack

- **Python 3.12**
- **FastAPI** - Modern async web framework
- **SQLAlchemy 2.0** - Async ORM
- **PostgreSQL + pgvector** - Database with vector support for AI
- **Redis** - Caching and task queue
- **Alembic** - Database migrations
- **Pydantic v2** - Data validation
- **JWT** - Authentication
- **bcrypt** - Password hashing

## Project Structure

```
backend/
├── app/
│   ├── api/v1/          # API endpoints
│   ├── core/            # Core configuration (config, database, security)
│   ├── models/          # SQLAlchemy models
│   ├── schemas/         # Pydantic schemas
│   ├── services/        # Business logic
│   └── main.py          # FastAPI app
├── alembic/             # Database migrations
├── tests/               # Tests
├── requirements.txt     # Production dependencies
└── Dockerfile           # Multi-stage Docker build
```

## Development

### Prerequisites

- Python 3.12+
- Docker & Docker Compose

### Local Development (Docker)

1. Copy environment variables:
   ```bash
   cp .env.example .env
   ```

2. Start development environment:
   ```bash
   docker compose -f docker-compose.yml -f docker-compose.dev.yml up
   ```

3. Access the API:
   - API: http://localhost:8000
   - Docs: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

### Local Development (Native)

1. Create virtual environment:
   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```

3. Run migrations:
   ```bash
   alembic upgrade head
   ```

4. Start development server:
   ```bash
   uvicorn app.main:app --reload
   ```

## Database Migrations

Create a new migration:
```bash
alembic revision --autogenerate -m "description"
```

Apply migrations:
```bash
alembic upgrade head
```

Rollback migration:
```bash
alembic downgrade -1
```

## Testing

Run all tests:
```bash
pytest
```

Run with coverage:
```bash
pytest --cov=app --cov-report=html
```

## Code Quality

Format and lint:
```bash
ruff check . --fix
ruff format .
```

Type checking:
```bash
mypy app/
```

## API Documentation

- OpenAPI/Swagger: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json

## Health Check

```bash
curl http://localhost:8000/api/v1/health
```

Response:
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

## Environment Variables

See `.env.example` for all available configuration options.

Key variables:
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `JWT_SECRET_KEY` - Secret for JWT tokens
- `ANTHROPIC_API_KEY` - Anthropic API key for AI features
- `CORS_ORIGINS` - Allowed CORS origins

## Production Deployment

Build production image:
```bash
docker build -t alice-backend:latest ./backend
```

Run production stack:
```bash
docker compose up -d
```

## Security

- Passwords are hashed with bcrypt
- JWT tokens for authentication
- CORS configured for specific origins
- Non-root Docker user
- SQL injection protection via SQLAlchemy
- Input validation via Pydantic

## License

Proprietary - HR Code Labs
