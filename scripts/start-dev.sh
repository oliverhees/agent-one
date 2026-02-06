#!/bin/bash
# Development startup script for ALICE

set -e

echo "🚀 Starting ALICE Development Environment..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running or you don't have permission."
    echo "   Please run: sudo usermod -aG docker $USER && newgrp docker"
    exit 1
fi

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env from .env.example..."
    cp .env.example .env
fi

# Build and start services
echo "🏗️  Building Docker images..."
docker compose build

echo "🚀 Starting services..."
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d

echo "⏳ Waiting for services to be healthy..."
sleep 10

# Check health
echo "🏥 Checking health..."
curl -f http://localhost:8000/api/v1/health || {
    echo "❌ Health check failed. Check logs with: docker compose logs api"
    exit 1
}

echo ""
echo "✅ ALICE Backend is running!"
echo ""
echo "📍 Endpoints:"
echo "   API:     http://localhost:8000"
echo "   Docs:    http://localhost:8000/docs"
echo "   ReDoc:   http://localhost:8000/redoc"
echo "   Health:  http://localhost:8000/api/v1/health"
echo ""
echo "🗄️  Services:"
echo "   PostgreSQL: localhost:5432"
echo "   Redis:      localhost:6379"
echo ""
echo "📋 Useful commands:"
echo "   View logs:     docker compose logs -f api"
echo "   Stop:          docker compose down"
echo "   Restart:       docker compose restart api"
echo "   Shell:         docker compose exec api bash"
echo ""
