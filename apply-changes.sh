#!/bin/bash

# This script is a helper to ensure the use of `./dev.sh rebuild-dev` instead of docker restart

echo "📝 Mercury Bank Development Best Practices"
echo "==========================================="
echo ""
echo "To apply changes to the application, ALWAYS use:"
echo ""
echo "    ./dev.sh rebuild-dev"
echo ""
echo "This will:"
echo "  1. Stop all containers"
echo "  2. Rebuild the Docker images"
echo "  3. Start all services"
echo "  4. Run migrations automatically"
echo ""
echo "ℹ️  After rebuild, you can use the new role-based user management:"
echo "   - ./dev.sh assign-role <username> <role>"
echo "   - ./dev.sh list-by-role <role>"
echo "   - ./dev.sh list-roles"
echo ""
echo "❌ NEVER use these commands for applying changes:"
echo "   - docker restart container-name"
echo "   - docker-compose restart"
echo ""
echo "ℹ️  Use this script to check the status of your services:"
echo ""

# Check if services are running
echo "Current Service Status:"
echo "----------------------"
docker-compose ps

echo ""
echo "Run './dev.sh rebuild-dev' now? (y/n)"
read -r answer

if [[ "$answer" == "y" || "$answer" == "Y" ]]; then
  echo "Running rebuild-dev..."
  ./dev.sh rebuild-dev
else
  echo "Cancelled. Remember to use ./dev.sh rebuild-dev when applying changes!"
fi
