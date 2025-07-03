#!/bin/bash

echo "🚀 Mercury Bank Platform Startup"
echo "================================"

# Check if Docker and Docker Compose are available
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed or not in PATH"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed or not in PATH"
    exit 1
fi

# Create logs directory if it doesn't exist
mkdir -p logs

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  No .env file found. Copying from .env.example..."
    cp .env.example .env
    echo "📝 Please edit .env file with your configuration before running again"
    exit 1
fi

echo "🔨 Building Docker images..."
docker-compose build

echo "🌟 Starting all services..."
docker-compose up -d

echo ""
echo "✅ Platform started successfully!"
echo ""
echo "📱 Web Interface: http://localhost:5001"
echo "🗄️  Database Admin: http://localhost:8080"
echo ""
echo "📊 View logs:"
echo "   All services: docker-compose logs -f"
echo "   Sync service: docker-compose logs -f mercury-sync"
echo "   Web app:      docker-compose logs -f web-app"
echo ""
echo "🛑 To stop: docker-compose down"
