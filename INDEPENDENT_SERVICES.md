# Independent Service Architecture

This document explains how the Mercury Bank platform is structured for independent Docker Hub publishing.

## 🏗️ Architecture Overview

Each service (`sync_app` and `web_app`) is **completely self-contained** and can be built, tested, and deployed independently. There are **no shared files** between services.

### Why Independent Services?

1. **Independent Publishing**: Each service publishes to Docker Hub separately via GitHub Actions
2. **Independent Scaling**: Services can be scaled independently based on needs
3. **Independent Development**: Teams can work on services without affecting each other
4. **Independent Deployment**: Services can be deployed to different environments separately

## 📁 Service Structure

### Sync Service (`sync_app/`)
```
sync_app/
├── models/              # Complete SQLAlchemy models (self-contained)
├── migrations/          # Database migrations specific to sync service
├── sync.py             # Main sync application
├── migration_manager.py # Migration management
├── health_check.py     # Health monitoring
├── Dockerfile          # Independent Docker build
├── requirements.txt    # Python dependencies
└── README.md          # Service-specific documentation
```

### Web Interface (`web_app/`)
```
web_app/
├── models/              # Complete SQLAlchemy models (self-contained)
├── migrations/          # Database migrations specific to web app
├── templates/           # HTML templates
├── app.py              # Flask web application
├── migration_manager.py # Migration management
├── Dockerfile          # Independent Docker build
├── requirements.txt    # Python dependencies
└── README.md           # Service-specific documentation
```

## 🚀 GitHub Actions Workflows

Each service has its own GitHub Actions workflow:

- **`.github/workflows/sync-service.yml`** - Builds and publishes sync service
- **`.github/workflows/web-interface.yml`** - Builds and publishes web interface

### Workflow Features:
- Triggers only on changes to respective service directory
- Builds from service-specific context (`./sync_app` or `./web_app`)
- Publishes to Docker Hub with proper tagging
- Supports both development and production branches

## 🐳 Docker Deployment Options

### Option 1: Production (Published Images)
```bash
# Update docker-compose.yml with your Docker Hub username
vim docker-compose.yml

# Start services using published images
make prod-up
```

### Option 2: Development (Local Builds)
```bash
# Build and start services locally
make dev
```

### Option 3: Individual Service Development
```bash
# Build specific service
make sync-build  # or make web-build

# Start specific service
make sync-up     # or make web-up
```

## 🔧 Configuration

### Docker Hub Publishing
1. Update `docker-compose.yml` with your Docker Hub username:
   ```yaml
   image: "your-dockerhub-username/mercury-bank-sync:latest"
   image: "your-dockerhub-username/mercury-bank-sync-gui:latest"
   ```

2. Set GitHub repository secrets:
   - `DOCKER_USERNAME` - Your Docker Hub username
   - `DOCKER_PASSWORD` - Your Docker Hub access token

### Independent Database Schemas
Each service manages its own database schema through migrations:
- Services share the same database but manage their own tables
- Each service runs its own migrations on startup
- No conflicts because each service owns specific tables

## 📋 Best Practices

### 1. Service Independence
- ✅ Each service has its own models, migrations, and dependencies
- ✅ No shared files between services
- ✅ Each service can be built independently
- ✅ Services are published to separate Docker Hub repositories

### 2. Development Workflow
- Work on services in their respective directories
- Test services independently
- Use `make dev` for local development with hot reloading
- Use `make prod-up` to test with published images

### 3. Database Management
- Each service runs its own migrations
- Services coordinate through database constraints, not shared code
- Use descriptive migration names to avoid conflicts

### 4. Deployment
- Services can be deployed independently
- Use environment variables for configuration
- Monitor services independently via their health endpoints

## 🚨 Important Notes

1. **No Shared Dependencies**: Each service includes all required dependencies in its own `requirements.txt`
2. **Independent Versioning**: Services are versioned and tagged independently
3. **Self-Contained Builds**: Each Dockerfile builds everything the service needs
4. **Database Coordination**: Services share a database but manage separate table sets

This architecture ensures maximum flexibility for development, testing, and deployment while maintaining clear service boundaries.
