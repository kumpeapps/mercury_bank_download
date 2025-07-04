#!/bin/bash

echo "🚀 Starting Mercury Bank Sync Service..."

# Run database migrations with Alembic
echo "🔄 Running database migrations..."
alembic upgrade head

# Start the sync service
echo "📊 Starting sync process..."
exec python sync.py
