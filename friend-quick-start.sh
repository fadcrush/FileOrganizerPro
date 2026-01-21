#!/bin/bash
# Quick Start Script for Friends
# Usage: bash friend-quick-start.sh

set -e

echo "🚀 FileOrganizer Pro - Friend Quick Start"
echo "=========================================="
echo ""

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Install from: https://docker.com/products/docker-desktop"
    exit 1
fi

echo "✅ Docker found"

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose not found. Installing..."
    exit 1
fi

echo "✅ Docker Compose found"
echo ""

# Clone if needed
if [ ! -d ".git" ]; then
    echo "📦 Repository not found. Clone first:"
    echo "   git clone https://github.com/[yourname]/FileOrganizerPro"
    echo "   cd FileOrganizerPro"
    exit 1
fi

# Create .env if needed
if [ ! -f ".env" ]; then
    echo "📄 Creating .env file..."
    cp .env.example .env
    echo "✅ .env created (edit if needed)"
fi

echo ""
echo "🚀 Starting FileOrganizer Pro..."
docker-compose up -d

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 5

# Check health
if curl -s http://localhost:8000/health | grep -q "ok"; then
    echo "✅ API is running!"
else
    echo "⏳ Services starting up... (wait a moment)"
    sleep 5
fi

echo ""
echo "=========================================="
echo "🎉 FileOrganizer Pro is ready!"
echo "=========================================="
echo ""
echo "📖 View API Docs:"
echo "   http://localhost:8000/docs"
echo ""
echo "📚 Alternative Docs:"
echo "   http://localhost:8000/redoc"
echo ""
echo "🧪 Test the API:"
echo "   curl http://localhost:8000/health"
echo ""
echo "⏹️  Stop Services:"
echo "   docker-compose down"
echo ""
echo "❌ Something broken?"
echo "   docker-compose logs -f app"
echo ""
