# Use Python 3.11 slim image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# Set working directory
WORKDIR /app

# Install system dependencies (this layer changes less frequently)
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    build-essential \
    libffi-dev \
    default-libmysqlclient-dev \
    pkg-config \
    python3-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better caching)
COPY requirements.txt /app/requirements.txt

# Install Python dependencies (this layer will be cached if requirements.txt doesn't change)
RUN pip install --upgrade pip && \
    pip install --no-cache-dir --prefer-binary -r /app/requirements.txt

# Copy the web app files (this layer changes most frequently, so put it last)
COPY . /app/

# Make health check script executable
RUN chmod +x /app/health_check.py

# Create a non-root user
RUN useradd --create-home --shell /bin/bash app
RUN chown -R app:app /app
RUN chmod +x /app/start_new.sh

# Expose port
EXPOSE 5000

# Switch to non-root user
USER app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python3 health_check.py || exit 1

# Run the application using the new SQLAlchemy-based startup script
CMD ["./start_new.sh"]
