#!/bin/bash
# Setup Test Database for ALICE Backend Tests
# This script creates/recreates the alice_test database in the running PostgreSQL instance

set -e

echo "======================================"
echo "ALICE Test Database Setup"
echo "======================================"
echo ""

# Check if docker compose is available
if ! command -v docker &> /dev/null; then
    echo "ERROR: docker is not installed or not in PATH"
    exit 1
fi

# Check if PostgreSQL container is running
if ! docker compose ps db | grep -q "Up"; then
    echo "ERROR: PostgreSQL container is not running"
    echo "Please start it first with: docker compose up -d db"
    exit 1
fi

echo "PostgreSQL container is running"
echo ""

# Drop test database if exists
echo "Dropping existing test database (if exists)..."
docker compose exec -T db psql -U alice -c "DROP DATABASE IF EXISTS alice_test;" 2>/dev/null || true

# Create test database
echo "Creating test database..."
docker compose exec -T db psql -U alice -c "CREATE DATABASE alice_test;"

# Install extensions
echo "Installing PostgreSQL extensions..."
docker compose exec -T db psql -U alice -d alice_test -c "CREATE EXTENSION IF NOT EXISTS vector;"
docker compose exec -T db psql -U alice -d alice_test -c "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";"
docker compose exec -T db psql -U alice -d alice_test -c "CREATE EXTENSION IF NOT EXISTS pg_trgm;"

echo ""
echo "======================================"
echo "Test database ready!"
echo "======================================"
echo ""
echo "Connection details:"
echo "  Host:     localhost"
echo "  Port:     5432"
echo "  Database: alice_test"
echo "  User:     alice"
echo "  Password: alice_dev_123"
echo ""
echo "You can now run tests with: pytest"
echo ""
