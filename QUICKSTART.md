# ALICE Backend - Quick Start Guide

Get the ALICE backend running in under 5 minutes.

## Prerequisites

- Docker installed and running
- Docker Compose v2+
- Docker permissions configured

## Start Development (3 Commands)

```bash
# 1. Ensure you have Docker permissions
sudo usermod -aG docker $USER && newgrp docker

# 2. Navigate to project
cd "/media/oliver/Platte 2 (Netac)/alice-adhs-coach"

# 3. Start everything
./scripts/start-dev.sh
```

**That's it!** The script will:
- Copy .env if needed
- Build Docker images
- Start all services
- Wait for health checks
- Verify everything is running

## Access Points

| Service | URL | Description |
|---------|-----|-------------|
| **API** | http://localhost:8000 | Root endpoint |
| **Docs** | http://localhost:8000/docs | Interactive API docs |
| **ReDoc** | http://localhost:8000/redoc | Alternative docs |
| **Health** | http://localhost:8000/api/v1/health | Health check |
| **PostgreSQL** | localhost:5432 | Database (user: alice, pass: alice_dev_123) |
| **Redis** | localhost:6379 | Cache |

## Test It

```bash
# Check health
curl http://localhost:8000/api/v1/health

# Expected response:
# {
#   "status": "healthy",
#   "version": "0.1.0",
#   "services": {
#     "db": "ok",
#     "redis": "ok"
#   }
# }
```

## Common Tasks

### View Logs
```bash
docker compose logs -f api
```

### Stop Everything
```bash
docker compose down
```

### Restart API Only
```bash
docker compose restart api
```

### Access API Shell
```bash
docker compose exec api bash
```

### Run Migrations
```bash
docker compose exec api alembic upgrade head
```

### Create Migration
```bash
docker compose exec api alembic revision --autogenerate -m "description"
```

## Manual Start (Without Script)

```bash
# Copy environment
cp .env.example .env

# Start services
docker compose -f docker-compose.yml -f docker-compose.dev.yml up

# In another terminal, check health
curl http://localhost:8000/api/v1/health
```

## Troubleshooting

### Docker Permission Denied
```bash
sudo usermod -aG docker $USER
newgrp docker
```

### Port Already in Use
```bash
# Find what's using port 8000
sudo lsof -i :8000

# Kill it or change port in docker-compose.yml
```

### Service Won't Start
```bash
# Check logs
docker compose logs api

# Rebuild
docker compose build --no-cache
docker compose up
```

### Database Connection Failed
```bash
# Check if database is running
docker compose ps db

# Check database logs
docker compose logs db
```

## Development Workflow

### 1. Make Code Changes
- Edit files in `backend/app/`
- Changes are auto-detected (hot-reload)
- No restart needed

### 2. Add New Dependency
```bash
# Add to requirements.txt
echo "package-name==version" >> backend/requirements.txt

# Rebuild
docker compose build api
docker compose up -d
```

### 3. Database Changes
```bash
# Edit model in backend/app/models/
# Create migration
docker compose exec api alembic revision --autogenerate -m "description"

# Apply migration
docker compose exec api alembic upgrade head
```

### 4. Run Tests (Coming Soon)
```bash
docker compose exec api pytest
docker compose exec api pytest --cov=app
```

## Connect to Database

### Using psql (inside container)
```bash
docker compose exec db psql -U alice -d alice
```

### Using External Client
```
Host: localhost
Port: 5432
Database: alice
Username: alice
Password: alice_dev_123
```

## Connect to Redis

```bash
docker compose exec redis redis-cli
```

## Environment Variables

Edit `.env` to customize:

```bash
# Change database password
POSTGRES_PASSWORD=your_secure_password

# Add API keys
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...

# Change JWT secret
JWT_SECRET_KEY=your-random-32-char-string
```

After changing `.env`:
```bash
docker compose down
docker compose up -d
```

## Next Steps

1. **Read the Docs**
   - `/backend/README.md` - Backend overview
   - `/backend/STRUCTURE.md` - Architecture details
   - `/docs/DEPLOYMENT.md` - Deployment guide

2. **Explore the API**
   - Visit http://localhost:8000/docs
   - Try the health endpoint
   - Check the OpenAPI schema

3. **Start Development**
   - Add your first model
   - Create a migration
   - Implement an endpoint
   - Write tests

## Help & Support

- **Documentation**: `/docs/` directory
- **Backend Docs**: `/backend/README.md`
- **Full Setup**: `/SETUP_COMPLETE.md`
- **Linear**: Check HR-26 for task details

---

**Quick Reference**:
```bash
# Start
./scripts/start-dev.sh

# Stop
docker compose down

# Logs
docker compose logs -f api

# Shell
docker compose exec api bash

# Migrations
docker compose exec api alembic upgrade head
```

---

**ALICE** - Proactive Personal Assistant
**HR Code Labs** - Vibe Coding Agency
