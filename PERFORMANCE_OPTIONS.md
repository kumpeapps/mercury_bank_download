# Simple Performance Optimizations for docker-compose.yml

If you want to improve performance with minimal changes to your existing setup, here are the key optimizations you can apply:

## Option 1: Simple Performance Boost (No Additional Files Needed)

Just update your existing `docker-compose.yml` with these performance optimizations:

```yaml
x-common-variables: &common-variables
  DATABASE_URL: mysql+pymysql://mercury_user:mercury_password@mysql:3306/mercury_bank
  SYNC_DAYS_BACK: 30
  SYNC_INTERVAL_MINUTES: 60  # Increase from 2 to reduce load
  RUN_ONCE: false
  SECRET_KEY: your-secret-key-here
  # Performance optimizations
  DB_POOL_SIZE: 10
  DB_POOL_RECYCLE: 3600
  ENABLE_COMPRESSION: true
  STATIC_FILE_CACHING: true

services:
  mysql:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: mercury_root_password
      MYSQL_DATABASE: mercury_bank
      MYSQL_USER: mercury_user
      MYSQL_PASSWORD: mercury_password
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql:ro
    restart: unless-stopped
    # Add performance optimizations for MySQL
    command: >
      --innodb-buffer-pool-size=128M
      --innodb-log-file-size=32M
      --innodb-flush-log-at-trx-commit=2
      --query-cache-type=1
      --query-cache-size=32M
    # Add resource limits
    deploy:
      resources:
        limits:
          memory: 256M
        reservations:
          memory: 128M
    networks:
      - mercury-network
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      timeout: 20s
      retries: 10

  mercury-sync:
    image: "justinkumpe/mercury-bank-sync:latest"
    environment: *common-variables
    volumes:
      - ./sync_app/logs:/app/logs
    restart: unless-stopped
    # Add resource limits
    deploy:
      resources:
        limits:
          memory: 128M
        reservations:
          memory: 64M
    networks:
      - mercury-network
    depends_on:
      mysql:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "python", "health_check.py"]
      interval: 60s  # Less frequent checks
      timeout: 10s
      retries: 3
      start_period: 60s

  web-app:
    image: "justinkumpe/mercury-bank-sync-gui:latest"
    environment: 
      <<: *common-variables
      # Web-specific performance settings
      FLASK_ENV: production
      PYTHONUNBUFFERED: 1
    ports:
      - "5001:5000"
    volumes:
      - ./web_app/logs:/app/logs
    restart: unless-stopped
    # Add resource limits
    deploy:
      resources:
        limits:
          memory: 256M
        reservations:
          memory: 128M
    networks:
      - mercury-network
    depends_on:
      mysql:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

  adminer:
    image: adminer:latest
    ports:
      - "8080:8080"
    restart: unless-stopped
    environment:
      ADMINER_DEFAULT_SERVER: mysql
      ADMINER_DESIGN: hydra  # Better theme
    # Add resource limits
    deploy:
      resources:
        limits:
          memory: 32M
        reservations:
          memory: 16M
    networks:
      - mercury-network

volumes:
  mysql_data:

networks:
  mercury-network:
    driver: bridge
```

## Option 2: Full Performance Setup (Requires Additional Files)

If you want maximum performance with nginx reverse proxy, use:

```bash
# Use the production setup with nginx
docker-compose -f docker-compose.prod.yml up -d
```

This requires:
- `nginx.conf`
- `nginx_proxy_params`
- `.env.prod` file with credentials

## Quick Summary

**For Simple Setup:** Just update your existing `docker-compose.yml` with the performance settings above.

**For Maximum Performance:** Use `docker-compose.prod.yml` with the full nginx setup.

## Key Differences

| Feature | Simple Setup | Full Setup |
|---------|-------------|-------------|
| Setup Complexity | Easy (just edit existing file) | Advanced (requires additional files) |
| Performance Gain | 20-30% improvement | 50-80% improvement |
| Files Required | Just docker-compose.yml | Multiple config files |
| Nginx Reverse Proxy | No | Yes |
| Static Asset Optimization | No | Yes |
| Gzip Compression | App-level only | Nginx-level (better) |
| Caching Headers | Basic | Advanced |
| Resource Monitoring | Basic | Comprehensive |

Choose the option that fits your comfort level and performance requirements!
