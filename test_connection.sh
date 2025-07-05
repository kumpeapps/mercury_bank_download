#!/bin/bash
# Connection test script for Mercury Bank Integration platform

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Mercury Bank Integration Platform - Connection Test${NC}"
echo "=================================================="
echo

# Test environment variables
echo -e "${YELLOW}Testing environment variables...${NC}"
if [ -z "$FLASK_APP_HOST" ]; then
  FLASK_APP_HOST="172.16.18.18"
  echo -e "${YELLOW}FLASK_APP_HOST not set, using default: ${FLASK_APP_HOST}${NC}"
else
  echo -e "${GREEN}FLASK_APP_HOST is set to: ${FLASK_APP_HOST}${NC}"
fi

if [ -z "$FLASK_APP_PORT" ]; then
  FLASK_APP_PORT="5001"
  echo -e "${YELLOW}FLASK_APP_PORT not set, using default: ${FLASK_APP_PORT}${NC}"
else
  echo -e "${GREEN}FLASK_APP_PORT is set to: ${FLASK_APP_PORT}${NC}"
fi

# Test network connectivity
echo
echo -e "${YELLOW}Testing network connectivity...${NC}"
if ping -c 1 -W 1 $FLASK_APP_HOST > /dev/null 2>&1; then
  echo -e "${GREEN}✓ Host ${FLASK_APP_HOST} is reachable${NC}"
else
  echo -e "${RED}✗ Host ${FLASK_APP_HOST} is not reachable${NC}"
  echo "Make sure the IP address is correct and the host is running"
fi

# Test TCP port connectivity
echo
echo -e "${YELLOW}Testing TCP port connectivity...${NC}"
if nc -z -w 1 $FLASK_APP_HOST $FLASK_APP_PORT > /dev/null 2>&1; then
  echo -e "${GREEN}✓ Port ${FLASK_APP_PORT} is open on ${FLASK_APP_HOST}${NC}"
else
  echo -e "${RED}✗ Port ${FLASK_APP_PORT} is closed on ${FLASK_APP_HOST}${NC}"
  echo "Make sure the Flask application is running and the port is correct"
fi

# Test HTTP connectivity
echo
echo -e "${YELLOW}Testing HTTP connectivity...${NC}"
HEALTH_CHECK=$(curl -s -o /dev/null -w "%{http_code}" http://${FLASK_APP_HOST}:${FLASK_APP_PORT}/health)
if [ "$HEALTH_CHECK" = "200" ]; then
  echo -e "${GREEN}✓ Health check endpoint returned 200 OK${NC}"
else
  echo -e "${RED}✗ Health check failed with status: ${HEALTH_CHECK}${NC}"
  echo "Make sure the Flask application is running and the health endpoint exists"
fi

# Test Nginx configuration
echo
echo -e "${YELLOW}Testing Nginx configuration...${NC}"
if command -v nginx > /dev/null 2>&1; then
  NGINX_TEST=$(nginx -t 2>&1)
  if echo "$NGINX_TEST" | grep -q "successful"; then
    echo -e "${GREEN}✓ Nginx configuration is valid${NC}"
  else
    echo -e "${RED}✗ Nginx configuration has errors:${NC}"
    echo "$NGINX_TEST"
  fi
else
  echo -e "${YELLOW}! Nginx command not found, skipping configuration test${NC}"
fi

# Summary
echo
echo -e "${YELLOW}Connection Test Summary${NC}"
echo "=================================================="
if ping -c 1 -W 1 $FLASK_APP_HOST > /dev/null 2>&1 && \
   nc -z -w 1 $FLASK_APP_HOST $FLASK_APP_PORT > /dev/null 2>&1 && \
   [ "$HEALTH_CHECK" = "200" ]; then
  echo -e "${GREEN}✓ All tests passed. Flask application should be reachable from Nginx.${NC}"
  echo "If you're still experiencing issues, please check the logs and headers."
else
  echo -e "${RED}✗ Some tests failed. Please fix the connectivity issues before proceeding.${NC}"
  echo "Refer to REVERSE_PROXY_TROUBLESHOOTING.md for more detailed steps."
fi

echo
echo "For more debugging options, add the debug routes from flask_proxy_debug.py"
echo "to your Flask application and access /debug/proxy through your reverse proxy."
