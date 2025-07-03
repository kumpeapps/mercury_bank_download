#!/bin/bash
# Mercury Bank Sync Service - CLI GUI Launcher
# This script launches the command-line interface for managing the sync service

# Check if we're in a Docker container
if [ -f /.dockerenv ]; then
    echo "Running inside Docker container"
    cd /app
    exec python cli_gui.py
else
    echo "Running outside Docker - launching via docker-compose"
    # Check if docker-compose.yml exists
    if [ ! -f docker-compose.yml ]; then
        echo "Error: docker-compose.yml not found. Please run from the project root directory."
        exit 1
    fi
    
    # Check if sync service is running
    if ! docker-compose ps mercury-sync | grep -q "Up"; then
        echo "Starting Mercury sync service..."
        docker-compose up -d mercury-sync
        echo "Waiting for service to be ready..."
        sleep 5
    fi
    
    echo "Launching CLI GUI..."
    exec docker-compose exec mercury-sync python cli_gui.py
fi
