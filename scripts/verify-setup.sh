#!/bin/bash
# Verification script for ALICE backend setup

set -e

echo "🔍 Verifying ALICE Backend Setup..."
echo ""

# Check Python version
echo "✓ Checking Python version..."
if command -v python3.12 &> /dev/null; then
    echo "  ✅ Python 3.12 found: $(python3.12 --version)"
else
    echo "  ⚠️  Python 3.12 not found. Install with: sudo apt install python3.12"
fi

# Check Docker
echo "✓ Checking Docker..."
if command -v docker &> /dev/null; then
    echo "  ✅ Docker found: $(docker --version)"
else
    echo "  ❌ Docker not found. Install from: https://docs.docker.com/engine/install/"
fi

# Check Docker Compose
echo "✓ Checking Docker Compose..."
if docker compose version &> /dev/null; then
    echo "  ✅ Docker Compose found: $(docker compose version)"
else
    echo "  ❌ Docker Compose not found."
fi

echo ""
echo "✓ Checking backend structure..."

# Critical files
files=(
    "backend/app/main.py"
    "backend/app/core/config.py"
    "backend/app/core/database.py"
    "backend/app/core/security.py"
    "backend/app/api/v1/health.py"
    "backend/requirements.txt"
    "backend/Dockerfile"
    "docker-compose.yml"
    ".env.example"
)

all_ok=true
for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✅ $file"
    else
        echo "  ❌ $file (missing)"
        all_ok=false
    fi
done

echo ""
if [ "$all_ok" = true ]; then
    echo "✅ All files present!"
    echo ""
    echo "📋 Next steps:"
    echo "   1. Ensure you have Docker permissions: sudo usermod -aG docker $USER"
    echo "   2. Log out and back in, or run: newgrp docker"
    echo "   3. Start development: ./scripts/start-dev.sh"
else
    echo "❌ Some files are missing. Please check the setup."
fi

echo ""
