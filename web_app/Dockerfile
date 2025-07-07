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
    nano \
    default-libmysqlclient-dev \
    curl \
    pkg-config \
    python3-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better caching)
COPY requirements.txt /app/requirements.txt

# Install Python dependencies (this layer will be cached if requirements.txt doesn't change)
RUN pip install --upgrade pip && \
    pip install --no-cache-dir --prefer-binary --only-binary=:all: -r /app/requirements.txt || \
    pip install --no-cache-dir --prefer-binary -r /app/requirements.txt

# Copy the web app files (this layer changes most frequently, so put it last)
COPY . /app/

# Make scripts executable
RUN chmod +x /app/health_check.py
RUN chmod +x /app/start.sh
RUN chmod +x /app/optimize_static_assets.sh
RUN chmod +x /app/update_template_assets.py

# Create static directory structure
RUN mkdir -p /app/static/{css,js,fonts,webfonts}

# Create a non-root user
RUN useradd --create-home --shell /bin/bash app
RUN chown -R app:app /app

# Expose port
EXPOSE 5000

# Switch to non-root user
USER app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python3 health_check.py || exit 1

# Run the application
CMD ["./start.sh"]
