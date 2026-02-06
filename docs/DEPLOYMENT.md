# ALICE Deployment Guide

Complete deployment guide for ALICE backend using Docker and Coolify.

## Prerequisites

- Docker 20.10+
- Docker Compose v2+
- PostgreSQL 16 (via pgvector/pgvector image)
- Redis 7+
- 2GB RAM minimum (4GB recommended)
- 10GB disk space

## Local Development

### Quick Start

1. **Clone and setup**
   ```bash
   git clone <repository>
   cd alice-adhs-coach
   cp .env.example .env
   ```

2. **Configure environment**
   Edit `.env` and set required variables:
   - `SECRET_KEY` - Random string (32+ chars)
   - `JWT_SECRET_KEY` - Random string (32+ chars)
   - `POSTGRES_PASSWORD` - Strong password
   - `ANTHROPIC_API_KEY` - Your Anthropic API key
   - `OPENAI_API_KEY` - Your OpenAI API key (optional)

3. **Start development environment**
   ```bash
   ./scripts/start-dev.sh
   ```

   Or manually:
   ```bash
   docker compose -f docker-compose.yml -f docker-compose.dev.yml up
   ```

4. **Verify health**
   ```bash
   curl http://localhost:8000/api/v1/health
   ```

### Development Features

- **Hot Reload**: Code changes trigger automatic reload
- **Volume Mounts**: Backend code is mounted for live editing
- **Debug Mode**: Detailed error messages and SQL logging
- **Exposed Ports**: Direct access to DB (5432) and Redis (6379)

## Production Deployment

### Docker Compose (Manual)

1. **Prepare environment**
   ```bash
   cp .env.example .env.production
   # Edit .env.production with production values
   ```

2. **Build production image**
   ```bash
   docker compose build
   ```

3. **Start services**
   ```bash
   docker compose up -d
   ```

4. **Run migrations**
   ```bash
   docker compose exec api alembic upgrade head
   ```

5. **Verify deployment**
   ```bash
   curl https://your-domain.com/api/v1/health
   ```

### Coolify Deployment

Coolify provides automated deployment with zero-downtime updates.

#### Prerequisites

- Coolify instance running
- GitHub repository configured
- Domain/subdomain configured in Coolify

#### Deployment Steps

1. **Create new application in Coolify**
   - Type: Docker Compose
   - Repository: Your GitHub repo
   - Branch: `main` (or `production`)

2. **Configure environment variables**
   Add all variables from `.env.example`:
   ```
   APP_ENV=production
   DEBUG=false
   SECRET_KEY=<strong-secret>
   JWT_SECRET_KEY=<strong-secret>
   POSTGRES_PASSWORD=<strong-password>
   ANTHROPIC_API_KEY=<your-key>
   CORS_ORIGINS=["https://your-domain.com"]
   ```

3. **Configure build settings**
   - Build Pack: Docker Compose
   - Dockerfile Path: `docker-compose.yml`
   - Port: 8000

4. **Configure health check**
   - Endpoint: `/api/v1/health`
   - Method: GET
   - Expected Status: 200
   - Interval: 30s
   - Timeout: 10s

5. **Configure domain**
   - Add your domain/subdomain
   - Enable SSL (Let's Encrypt)
   - Enable Force HTTPS

6. **Deploy**
   - Click "Deploy"
   - Watch build logs
   - Wait for health check to pass

#### Post-Deployment

1. **Run initial migration**
   ```bash
   # Via Coolify console or SSH
   docker compose exec api alembic upgrade head
   ```

2. **Verify services**
   ```bash
   curl https://your-domain.com/api/v1/health
   ```

3. **Check logs**
   ```bash
   docker compose logs -f api
   ```

## Database Migrations

### Create Migration

```bash
# Development
docker compose exec api alembic revision --autogenerate -m "description"

# Local (without Docker)
cd backend
alembic revision --autogenerate -m "description"
```

### Apply Migrations

```bash
# Production
docker compose exec api alembic upgrade head

# Specific version
docker compose exec api alembic upgrade <revision>
```

### Rollback Migration

```bash
# Rollback one step
docker compose exec api alembic downgrade -1

# Rollback to specific version
docker compose exec api alembic downgrade <revision>
```

## Monitoring & Maintenance

### Health Checks

The `/api/v1/health` endpoint checks:
- API status
- PostgreSQL connection
- Redis connection

Response format:
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

### Logs

**View all logs**
```bash
docker compose logs
```

**Follow API logs**
```bash
docker compose logs -f api
```

**View database logs**
```bash
docker compose logs -f db
```

### Backups

#### Database Backup

**Manual backup**
```bash
docker compose exec db pg_dump -U alice -d alice > backup_$(date +%Y%m%d_%H%M%S).sql
```

**Automated backup (add to crontab)**
```bash
0 2 * * * cd /path/to/alice && docker compose exec -T db pg_dump -U alice -d alice | gzip > /backups/alice_$(date +\%Y\%m\%d).sql.gz
```

#### Redis Backup

Redis automatically creates `dump.rdb` in the `redis_data` volume.

**Manual backup**
```bash
docker compose exec redis redis-cli BGSAVE
docker cp alice-redis:/data/dump.rdb ./redis_backup_$(date +%Y%m%d).rdb
```

### Restore

**Database restore**
```bash
docker compose exec -T db psql -U alice -d alice < backup.sql
```

**Redis restore**
```bash
docker compose stop redis
docker cp redis_backup.rdb alice-redis:/data/dump.rdb
docker compose start redis
```

## Security Checklist

- [ ] Change all default passwords
- [ ] Set strong `SECRET_KEY` (32+ random chars)
- [ ] Set strong `JWT_SECRET_KEY` (32+ random chars)
- [ ] Configure CORS origins to specific domains only
- [ ] Enable HTTPS/SSL (Let's Encrypt via Coolify)
- [ ] Restrict database access (firewall rules)
- [ ] Enable Redis authentication in production
- [ ] Regular backups configured
- [ ] Update Docker images regularly
- [ ] Monitor logs for suspicious activity
- [ ] Set up rate limiting (future enhancement)
- [ ] Configure CSP headers (future enhancement)

## Troubleshooting

### Container won't start

**Check logs**
```bash
docker compose logs api
```

**Common issues:**
- Database not ready → Wait for health check
- Port already in use → Change port in docker-compose.yml
- Environment variables missing → Check .env file

### Database connection failed

**Check database is running**
```bash
docker compose ps db
```

**Test connection**
```bash
docker compose exec db psql -U alice -d alice -c "SELECT 1;"
```

**Check DATABASE_URL format**
```
postgresql+asyncpg://user:password@host:port/database
```

### Redis connection failed

**Check Redis is running**
```bash
docker compose ps redis
```

**Test connection**
```bash
docker compose exec redis redis-cli ping
# Should return: PONG
```

### Health check failing

**Check individual services**
```bash
# API
curl http://localhost:8000/

# Database
docker compose exec db pg_isready -U alice

# Redis
docker compose exec redis redis-cli ping
```

### Migration failed

**Check migration history**
```bash
docker compose exec api alembic current
docker compose exec api alembic history
```

**Reset to specific version**
```bash
docker compose exec api alembic downgrade <revision>
```

## Performance Tuning

### PostgreSQL

Edit `docker-compose.yml`:
```yaml
db:
  environment:
    POSTGRES_MAX_CONNECTIONS: 100
  deploy:
    resources:
      limits:
        memory: 2G
```

### Redis

Edit `docker-compose.yml`:
```yaml
redis:
  command: redis-server --maxmemory 512mb --maxmemory-policy allkeys-lru
```

### API

Edit `docker-compose.yml`:
```yaml
api:
  deploy:
    resources:
      limits:
        cpus: '2'
        memory: 2G
```

For production, consider:
- Using gunicorn instead of uvicorn
- Multiple worker processes
- Connection pooling
- Caching strategies

## Scaling

### Horizontal Scaling (Multiple API Instances)

```yaml
api:
  deploy:
    replicas: 3
```

Add load balancer (nginx) in front:
```yaml
nginx:
  image: nginx:alpine
  ports:
    - "80:80"
  volumes:
    - ./nginx.conf:/etc/nginx/nginx.conf
```

### Vertical Scaling (Resource Limits)

Adjust resource limits per service as needed.

## Support

- Documentation: `/docs/`
- API Docs: `https://your-domain.com/docs`
- GitHub Issues: `<repository>/issues`
- Team: HR Code Labs

---

**Last Updated**: 2026-02-06
**Version**: 0.1.0
