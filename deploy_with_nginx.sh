#!/bin/bash

# Script to deploy the Nginx reverse proxy configuration for Mercury Bank Integration

# Color codes for better readability
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Mercury Bank Integration - Nginx Reverse Proxy Setup${NC}"
echo "============================================="

# Ensure the nginx directories exist
echo "Creating Nginx configuration directories..."
mkdir -p nginx/conf.d
mkdir -p nginx/ssl

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Error: docker-compose is not installed. Please install it first.${NC}"
    exit 1
fi

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo -e "${RED}Error: Docker is not running. Please start Docker first.${NC}"
    exit 1
fi

# Stop existing services
echo "Stopping existing services..."
docker-compose down

# Deploy with Nginx
echo "Starting services with Nginx as reverse proxy..."
docker-compose -f docker-compose.yml -f docker-compose.nginx.yml up -d

# Check if the services are running
if [ $? -eq 0 ]; then
    echo -e "${GREEN}Success! Services started with Nginx reverse proxy.${NC}"
    echo ""
    echo "Your application should now be accessible at:"
    echo "  http://localhost"
    echo ""
    echo "If you're using a custom domain, make sure it points to this server."
    echo ""
    echo -e "${YELLOW}Note:${NC} If you're using HTTPS, you'll need to place your SSL certificates in the nginx/ssl directory"
    echo "and uncomment the SSL section in the Nginx configuration."
else
    echo -e "${RED}Error: Failed to start services. Check the logs for more information.${NC}"
    echo "You can view the logs with: docker-compose -f docker-compose.yml -f docker-compose.nginx.yml logs"
fi
