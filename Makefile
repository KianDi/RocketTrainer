# RocketTrainer Development Makefile

.PHONY: help setup start stop build test clean logs shell migrate seed

# Default target
help:
	@echo "RocketTrainer Development Commands:"
	@echo ""
	@echo "  setup     - Initial project setup"
	@echo "  start     - Start development environment"
	@echo "  stop      - Stop all services"
	@echo "  build     - Build all Docker images"
	@echo "  test      - Run all tests"
	@echo "  clean     - Clean up containers and volumes"
	@echo "  logs      - Show logs for all services"
	@echo "  shell     - Open shell in API container"
	@echo "  migrate   - Run database migrations"
	@echo "  seed      - Seed database with initial data"

# Initial setup
setup:
	@echo "Setting up RocketTrainer development environment..."
	@cp .env.example .env || echo ".env already exists"
	@docker-compose build
	@docker-compose up -d db redis
	@sleep 5
	@docker-compose run --rm api alembic upgrade head
	@docker-compose run --rm api python scripts/seed_data.py
	@echo "Setup complete! Run 'make start' to start the development server."

# Start development environment
start:
	@echo "Starting RocketTrainer development environment..."
	@docker-compose up -d
	@echo "Services started!"
	@echo "API: http://localhost:8000"
	@echo "Frontend: http://localhost:3000"
	@echo "API Docs: http://localhost:8000/docs"

# Stop all services
stop:
	@echo "Stopping all services..."
	@docker-compose down

# Build all images
build:
	@echo "Building Docker images..."
	@docker-compose build

# Run tests
test:
	@echo "Running backend tests..."
	@docker-compose run --rm api pytest
	@echo "Running frontend tests..."
	@docker-compose run --rm frontend npm test -- --coverage --watchAll=false

# Clean up
clean:
	@echo "Cleaning up containers and volumes..."
	@docker-compose down -v
	@docker system prune -f

# Show logs
logs:
	@docker-compose logs -f

# Open shell in API container
shell:
	@docker-compose exec api bash

# Run database migrations
migrate:
	@echo "Running database migrations..."
	@docker-compose run --rm api alembic upgrade head

# Seed database
seed:
	@echo "Seeding database with initial data..."
	@docker-compose run --rm api python scripts/seed_data.py

# Development helpers
dev-api:
	@docker-compose up api db redis

dev-frontend:
	@docker-compose up frontend

# Production build
prod-build:
	@echo "Building production images..."
	@docker-compose -f docker-compose.prod.yml build

# Health check
health:
	@echo "Checking service health..."
	@curl -f http://localhost:8000/health || echo "API not responding"
	@curl -f http://localhost:3000 || echo "Frontend not responding"
