# Mercury Bank Data Synchronization

A Docker-based service for synchronizing accounts and transactions from Mercury Bank API to a MySQL database using SQLAlchemy. This service automatically handles creating new records and updating existing ones.

## Features

- 🏦 **Account Synchronization**: Fetches and syncs Mercury Bank accounts
- 💰 **Transaction Synchronization**: Fetches and syncs transactions with configurable date ranges
- 🔄 **Automatic Updates**: Overrides existing records with latest data from Mercury Bank
- 🐳 **Docker Support**: Fully containerized with Docker Compose
- 📊 **MySQL Database**: Persistent storage with proper indexing
- 🔍 **Configurable Sync**: Adjustable sync intervals and date ranges
- 📝 **Comprehensive Logging**: Detailed logs for monitoring and debugging
- 🏥 **Health Checks**: Built-in health monitoring

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Mercury Bank API key

### Setup

1. **Clone and navigate to the project**:
   ```bash
   cd mercury_bank_download
   ```

2. **Create environment file**:
   ```bash
   cp .env.example .env
   ```

3. **Edit the `.env` file** with your configuration:
   ```env
   MERCURY_API_KEY=your_actual_api_key_here
   MYSQL_ROOT_PASSWORD=your_secure_root_password
   MYSQL_PASSWORD=your_secure_mercury_password
   SYNC_DAYS_BACK=30
   SYNC_INTERVAL_MINUTES=60
   RUN_ONCE=false
   ```

4. **Start the services**:
   ```bash
   docker-compose up -d
   ```

5. **Check the logs**:
   ```bash
   docker-compose logs -f mercury-sync
   ```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MERCURY_API_KEY` | Your Mercury Bank API key | Required |
| `MERCURY_API_URL` | Mercury Bank API URL | `https://api.mercury.com` |
| `SYNC_DAYS_BACK` | Number of days back to sync transactions | `30` |
| `SYNC_INTERVAL_MINUTES` | Minutes between sync runs | `60` |
| `RUN_ONCE` | Run sync once and exit (true/false) | `false` |
| `MYSQL_ROOT_PASSWORD` | MySQL root password | Required |
| `MYSQL_PASSWORD` | MySQL mercury user password | Required |

## Database Schema

### Accounts Table
- `id` (Primary Key): Mercury account ID
- `name`: Account name
- `account_number`: Account number (unique)
- `routing_number`: Bank routing number
- `account_type`: Type of account
- `status`: Account status
- `balance`: Current balance
- `available_balance`: Available balance
- `currency`: Currency code (default: USD)
- `is_active`: Active status
- `created_at`: Record creation timestamp
- `updated_at`: Last update timestamp

### Transactions Table
- `id` (Primary Key): Mercury transaction ID
- `account_id` (Foreign Key): Reference to accounts table
- `amount`: Transaction amount
- `currency`: Currency code
- `description`: Transaction description
- `transaction_type`: Type of transaction (debit/credit)
- `status`: Transaction status
- `category`: Transaction category
- `counterparty_name`: Name of counterparty
- `counterparty_account`: Counterparty account info
- `reference_number`: Reference number
- `posted_at`: When transaction was posted
- `created_at`: Record creation timestamp
- `updated_at`: Last update timestamp

## Usage Examples

### Run Once Mode
To run synchronization once and exit:
```bash
echo "RUN_ONCE=true" >> .env
docker-compose up mercury-sync
```

### Continuous Mode
For continuous synchronization (default):
```bash
docker-compose up -d
```

### Custom Sync Interval
To sync every 30 minutes:
```bash
echo "SYNC_INTERVAL_MINUTES=30" >> .env
docker-compose restart mercury-sync
```

### Sync More Transaction History
To sync last 90 days of transactions:
```bash
echo "SYNC_DAYS_BACK=90" >> .env
docker-compose restart mercury-sync
```

## Monitoring

### View Logs
```bash
# View real-time logs
docker-compose logs -f mercury-sync

# View database logs
docker-compose logs -f db

# View last 100 lines
docker-compose logs --tail=100 mercury-sync
```

### Check Service Status
```bash
docker-compose ps
```

### Database Access
```bash
# Connect to MySQL
docker-compose exec db mysql -u mercury -p mercury_bank

# Or use any MySQL client with:
# Host: localhost
# Port: 3306
# Database: mercury_bank
# Username: mercury
# Password: (from your .env file)
```

## Troubleshooting

### Common Issues

1. **API Key Invalid**:
   - Verify your Mercury Bank API key in `.env`
   - Check API key permissions

2. **Database Connection Issues**:
   - Ensure MySQL container is healthy: `docker-compose ps`
   - Check database logs: `docker-compose logs db`

3. **Sync Errors**:
   - Check application logs: `docker-compose logs mercury-sync`
   - Verify network connectivity to Mercury Bank API

### Reset Everything
```bash
# Stop services and remove data
docker-compose down -v

# Rebuild and restart
docker-compose up --build -d
```

## Development

### Project Structure
```
mercury_bank_download/
├── models/
│   ├── __init__.py
│   ├── base.py
│   ├── account.py
│   └── transaction.py
├── sync.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── init.sql
├── .env.example
└── README.md
```

### Running Locally
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export MERCURY_API_KEY=your_key
export DATABASE_URL=mysql+pymysql://user:pass@localhost/mercury_bank

# Run sync
python sync.py
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

See LICENSE file for details.
