#!/bin/bash
# Phase 3 Backend Setup Script

echo "🚀 FileOrganizer Pro SaaS - Backend Setup"
echo "=========================================="
echo ""

# Check Python version
python_version=$(python --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $python_version"

# Install backend dependencies
echo ""
echo "📦 Installing backend dependencies..."
pip install -r requirements-backend.txt

echo ""
echo "✓ Installation complete!"
echo ""
echo "🚀 Next steps:"
echo "1. Setup PostgreSQL: docker run -e POSTGRES_USER=fileorg_user -e POSTGRES_PASSWORD=fileorg_pass -e POSTGRES_DB=fileorganizer_pro -p 5432:5432 -d postgres:15"
echo "2. Create .env file with DATABASE_URL and SECRET_KEY"
echo "3. Run: cd src/backend && python -m uvicorn api.main:app --reload"
echo "4. Open http://localhost:8000/docs for API documentation"
