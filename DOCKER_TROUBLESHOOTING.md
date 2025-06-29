# Docker Build Troubleshooting Guide

## The Error
You're getting a 401 Unauthorized error when trying to pull the Python base image from Docker Hub. This is commonly caused by:

1. Docker Hub rate limiting for anonymous users
2. Docker authentication issues
3. Network connectivity problems
4. Docker daemon configuration issues

## Solutions (try in order)

### Solution 1: Login to Docker Hub
```bash
# Login to Docker Hub (create free account if needed)
docker login

# Then try building again
docker build -t mercury_bank_download:latest-beta .
```

### Solution 2: Clear Docker Auth and Restart
```bash
# Logout and clear credentials
docker logout

# Restart Docker Desktop
# Then try building without login (anonymous access)
docker build -t mercury_bank_download:latest-beta .
```

### Solution 3: Use Alternative Base Image
Edit your Dockerfile to use a different registry:

```dockerfile
# Option A: Use GitHub Container Registry
FROM ghcr.io/python/python:3.11-slim

# Option B: Use Amazon ECR Public Gallery
FROM public.ecr.aws/docker/library/python:3.11-slim

# Option C: Use Microsoft Container Registry
FROM mcr.microsoft.com/mirror/docker/library/python:3.11-slim
```

### Solution 4: Build with No Cache
```bash
# Force a clean build
docker build --no-cache -t mercury_bank_download:latest-beta .
```

### Solution 5: Alternative Dockerfile (No Docker Hub dependency)
Create an alternative Dockerfile using a different approach:

```dockerfile
# Use Ubuntu base and install Python manually
FROM ubuntu:22.04

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Install Python and dependencies
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3.11-dev \
    python3-pip \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Create symlinks for python commands
RUN ln -s /usr/bin/python3.11 /usr/bin/python
RUN ln -s /usr/bin/pip3 /usr/bin/pip

# Rest of your Dockerfile remains the same...
WORKDIR /app
RUN mkdir -p /app/logs
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["python", "sync.py"]
```

## Quick Fix Commands

Try these commands in sequence:

```bash
# 1. Restart Docker Desktop completely
# 2. Clear Docker system
docker system prune -a

# 3. Try building with verbose output
docker build --progress=plain -t mercury_bank_download:latest-beta .

# 4. If still failing, try with different registry
docker build -t mercury_bank_download:latest-beta . --build-arg BASE_IMAGE=public.ecr.aws/docker/library/python:3.11-slim
```

## If All Else Fails

You can also run the application without Docker:

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate     # On Windows

# Install dependencies
pip install -r requirements.txt

# Run the sync script directly
python sync.py
```

## Network Issues

If you're behind a corporate firewall:

```bash
# Check if you can reach Docker Hub
curl -I https://registry-1.docker.io/v2/

# Configure Docker to use proxy if needed
# Edit ~/.docker/config.json or Docker Desktop settings
```

Try Solution 1 first (docker login), as this resolves the issue in most cases.
