# Mercury Bank Sync Service

This service handles synchronizing Mercury Bank transaction data to the database.

## Features

- Automatic transaction synchronization
- Support for multiple Mercury accounts
- Configurable sync intervals
- Database migration management
- Health monitoring

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Database connection string | Required |
| `MERCURY_SANDBOX_MODE` | Enable sandbox mode | `true` |
| `SYNC_DAYS_BACK` | Days to sync back | `30` |
| `SYNC_INTERVAL_MINUTES` | Sync interval in minutes | `2` |
| `RUN_ONCE` | Run once and exit | `false` |

## Usage

### Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
python migration_manager.py

# Start sync service
python sync.py
```

### Production (Docker)
```bash
# Build the image
docker-compose build

# Start the service
docker-compose up -d

# View logs
docker-compose logs -f mercury-sync
```

## Database Migrations

The service automatically runs database migrations on startup. Manual migration management:

```bash
# Run migrations
python migration_manager.py

# View migration status
python migration_manager.py --status
```
