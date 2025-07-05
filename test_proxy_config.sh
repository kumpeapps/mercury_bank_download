#!/bin/bash
# Helper script for testing the Flask application with reverse proxy settings

echo "Rebuilding Mercury Bank Integration Platform with reverse proxy settings..."

# Stop existing containers
echo "Step 1: Stopping existing containers..."
docker-compose down

# Build the images
echo "Step 2: Building images..."
docker-compose -f docker-compose.yml -f docker-compose.dev.yml -f docker-compose.proxy-test.yml build

# Start with proxy test configuration
echo "Step 3: Starting containers with proxy test configuration..."
docker-compose -f docker-compose.yml -f docker-compose.dev.yml -f docker-compose.proxy-test.yml up -d

echo "✅ Services started with reverse proxy configuration!"
echo ""
echo "Web application is now running with these settings:"
echo "  - SECURE_COOKIES=true"
echo "  - PREFERRED_URL_SCHEME=https"
echo "  - ProxyFix middleware enabled"
echo ""
echo "Access via Nginx at: https://mercury.vm.kumpeapps.com"
echo "Or directly at: http://localhost:5001"
echo ""
echo "Run ./test_connection.sh to verify connectivity"
