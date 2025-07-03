#!/bin/bash

echo "🚀 Starting Mercury Bank Sync Service..."

# Run migrations
echo "🔄 Running database migrations..."
python migration_manager.py

# Start the sync service
echo "📊 Starting sync process..."
exec python sync.py
