#!/bin/bash

# RocketTrainer E2E Test Runner
# Runs Playwright tests against the Docker environment

set -e

echo "🚀 RocketTrainer E2E Test Runner"
echo "================================"

# Check if Docker services are running
echo "📋 Checking Docker services..."
if ! docker-compose ps | grep -q "Up"; then
    echo "❌ Docker services are not running. Please start them with:"
    echo "   docker-compose up -d"
    exit 1
fi

# Check if frontend is accessible
echo "🌐 Checking frontend accessibility..."
if ! curl -s http://localhost:3000 > /dev/null; then
    echo "❌ Frontend not accessible at http://localhost:3000"
    echo "   Please ensure Docker services are running and healthy"
    exit 1
fi

# Check if backend is accessible
echo "🔧 Checking backend accessibility..."
if ! curl -s http://localhost:8000/health > /dev/null; then
    echo "❌ Backend not accessible at http://localhost:8000"
    echo "   Please ensure Docker services are running and healthy"
    exit 1
fi

echo "✅ All services are accessible"

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing test dependencies..."
    npm install
fi

# Install Playwright browsers if needed
echo "🎭 Ensuring Playwright browsers are installed..."
npx playwright install --with-deps

# Create test results directory
mkdir -p test-results/screenshots

# Run tests based on arguments
if [ "$1" = "headed" ]; then
    echo "🎭 Running tests in headed mode..."
    npx playwright test --headed
elif [ "$1" = "debug" ]; then
    echo "🐛 Running tests in debug mode..."
    npx playwright test --debug
elif [ "$1" = "ui" ]; then
    echo "🖥️  Opening Playwright UI..."
    npx playwright test --ui
else
    echo "🧪 Running all tests..."
    npx playwright test
fi

echo ""
echo "📊 Test Results:"
echo "   - Screenshots: test-results/screenshots/"
echo "   - HTML Report: playwright-report/index.html"
echo "   - Videos: test-results/ (on failures)"

# Open HTML report if tests completed
if [ -f "playwright-report/index.html" ]; then
    echo ""
    echo "🌐 To view detailed results, open: playwright-report/index.html"
fi
