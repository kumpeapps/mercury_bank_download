# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy the web app files
COPY . /app/

# Expose port
EXPOSE 5000

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# Create a non-root user
RUN useradd --create-home --shell /bin/bash app
RUN chown -R app:app /app
RUN chmod +x /app/start_new.sh
USER app

# Run the application using the new SQLAlchemy-based startup script
CMD ["./start_new.sh"]
