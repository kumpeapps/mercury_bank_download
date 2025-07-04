# Use Python 3.11 slim image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Create app directory
WORKDIR /app

# Install system dependencies (this layer changes less frequently)
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    nano \
    build-essential \
    default-libmysqlclient-dev \
    pkg-config \
    libffi-dev \
    python3-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create logs directory
RUN mkdir -p /app/logs

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies (this layer will be cached if requirements.txt doesn't change)
RUN pip install --upgrade pip && \
    pip install --no-cache-dir --prefer-binary --only-binary=:all: -r requirements.txt || \
    pip install --no-cache-dir --prefer-binary -r requirements.txt

# Copy application code (this layer changes most frequently, so put it last)
COPY . .

# Create a non-root user and set proper permissions
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app && \
    chmod -R 755 /app && \
    chmod +x /app/*.py && \
    chmod +x /app/start_sync.sh

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=5m --timeout=30s --start-period=30s --retries=3 \
    CMD python health_check.py

# Default command
CMD ["./start_sync.sh"]
