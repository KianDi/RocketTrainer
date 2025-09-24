#!/bin/bash

# RocketTrainer Setup Script
# This script sets up the development environment for RocketTrainer

set -e

echo "🚀 RocketTrainer Setup Script"
echo "=============================="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    echo "   Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    echo "   Visit: https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✅ Docker and Docker Compose are installed"

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "✅ .env file created"
    echo "⚠️  Please edit .env file and add your API keys:"
    echo "   - BALLCHASING_API_KEY (get from https://ballchasing.com/upload)"
    echo "   - STEAM_API_KEY (get from https://steamcommunity.com/dev/apikey)"
else
    echo "✅ .env file already exists"
fi

# Build Docker images
echo "🏗️  Building Docker images..."
docker-compose build

# Start database and Redis first
echo "🗄️  Starting database and Redis..."
docker-compose up -d db redis

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
sleep 10

# Run database migrations
echo "🔄 Running database migrations..."
docker-compose run --rm api alembic upgrade head

# Seed database with training packs
echo "🌱 Seeding database with training packs..."
docker-compose run --rm api python scripts/seed_data.py

# Start all services
echo "🚀 Starting all services..."
docker-compose up -d

# Wait a moment for services to start
sleep 5

# Check if services are running
echo "🔍 Checking service health..."

# Check API health
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ API is running at http://localhost:8000"
    echo "📚 API Documentation: http://localhost:8000/docs"
else
    echo "⚠️  API might still be starting up..."
fi

# Check frontend
if curl -f http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ Frontend is running at http://localhost:3000"
else
    echo "⚠️  Frontend might still be starting up..."
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file and add your API keys"
echo "2. Visit http://localhost:3000 to access RocketTrainer"
echo "3. Visit http://localhost:8000/docs for API documentation"
echo ""
echo "Useful commands:"
echo "  make start    - Start all services"
echo "  make stop     - Stop all services"
echo "  make logs     - View service logs"
echo "  make test     - Run tests"
echo "  make help     - Show all available commands"
echo ""
echo "For more information, see README.md"
