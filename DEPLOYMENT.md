# Deployment Guide

This document explains how to deploy the Mercury Bank platform using the reorganized structure.

## Overview

The platform is now split into two independent services:

- **Sync Service** (`sync_app/`) - Handles Mercury Bank API synchronization
- **Web Interface** (`web_app/`) - Provides the user dashboard and management interface

Each service is completely self-contained with its own:
- Docker container
- Dependencies (`requirements.txt`)
- Database models and migrations
- GitHub Actions workflow for automated building

## Deployment Options

### 1. Production (Recommended)

Uses pre-built Docker Hub images:

```bash
# Update docker-compose.yml with your Docker Hub username
# Replace "your-dockerhub-username" with your actual username

make prod-up
```

### 2. Development

Builds images locally:

```bash
make dev
```

### 3. Individual Services

Deploy services separately:

```bash
# Sync service only
cd sync_app && docker-compose up -d

# Web interface only  
cd web_app && docker-compose up -d
```

## GitHub Actions

The repository includes workflows to automatically build and push images to Docker Hub:

- `.github/workflows/sync-service.yml` - Builds sync service
- `.github/workflows/web-interface.yml` - Builds web interface

### Setup Requirements

1. Set these secrets in your GitHub repository:
   - `DOCKER_USERNAME` - Your Docker Hub username
   - `DOCKER_PASSWORD` - Your Docker Hub password/token

2. Images will be pushed as:
   - `your-username/mercury-bank-sync:latest`
   - `your-username/mercury-bank-sync-gui:latest`

## Environment Configuration

Each service can be configured independently:

### Sync Service
See `sync_app/.env.example` for available options.

### Web Interface  
See `web_app/.env.example` for available options.

## Make Commands

```bash
# Production deployment
make prod-up              # Start with published images
make logs                 # View logs
make down                 # Stop services

# Development
make dev                  # Build and start locally
make build                # Build images only

# Individual services
make sync-up             # Start sync service only
make web-up              # Start web interface only
make sync-logs           # Sync service logs
make web-logs            # Web interface logs
```
