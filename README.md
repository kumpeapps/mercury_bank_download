I used AI to write this readme file, it does have errors and I will re-write it as soon as I have a chance.

# Mercury Bank Integration Platform

A comprehensive platform for Mercury Bank data synchronization and management, consisting of two main components:

1. **Sync Service** (`sync_app/`) - Automated data synchronization from Mercury Bank API
2. **Web Interface** (`web_app/`) - User-friendly web dashboard for data management and reporting

## 🏗️ Project Structure

```
mercury_bank_download/
├── sync_app/                    # Mercury Bank sync service
│   ├── models/                  # Database models
│   ├── migrations/              # Database migrations
│   ├── sync.py                  # Main sync application
│   ├── migration_manager.py     # Migration management
│   ├── Dockerfile              # Sync service container
│   ├── docker-compose.yml      # Sync service compose
│   ├── requirements.txt        # Python dependencies
│   └── README.md               # Sync service documentation
├── web_app/                     # Web interface
│   ├── models/                  # Database models (shared schema)
│   ├── migrations/              # Web app migrations
│   ├── templates/               # HTML templates
│   ├── app.py                   # Flask web application
│   ├── Dockerfile              # Web app container
│   ├── docker-compose.yml      # Web app compose
│   ├── requirements.txt        # Python dependencies
│   └── README.md               # Web app documentation
├── docker-compose.yml          # Main orchestration file
└── README.md                   # This file
```

## ✨ Features

### Sync Service (`sync_app/`)
- 🏦 **Account Synchronization** - Automated Mercury Bank account syncing
- 💳 **Transaction Processing** - Real-time transaction data synchronization
- 🧪 **Sandbox Support** - Built-in testing environment support
- 🔄 **Automatic Migrations** - Database schema updates handled automatically
- ⚙️ **Configurable Sync** - Flexible scheduling and data range options
- 📝 **Comprehensive Logging** - Detailed monitoring and debugging
- 🏥 **Health Monitoring** - Built-in health checks and status reporting

### Web Interface (`web_app/`)
- 👥 **Multi-User Support** - Role-based user management and authentication
- 🔐 **Granular Access Control** - Account-level permissions and restrictions
- 📊 **Interactive Dashboard** - Real-time financial data visualization
- 💰 **Transaction Management** - Search, filter, and categorize transactions
- 📈 **Reporting & Analytics** - Charts, trends, and financial insights
- 🎯 **Default Account Settings** - User-customizable default views
- 📱 **Responsive Design** - Works on desktop, tablet, and mobile devices

## 🚀 Quick Start

### Prerequisites

- **Docker & Docker Compose** (recommended)
- **Mercury Bank API Key** ([Get yours here](https://mercury.com/developers))
- **Database Server** - MySQL, PostgreSQL, or other SQLAlchemy-supported database

### Option 1: Production Deployment (Recommended)

Use pre-built Docker Hub images for production:

```bash
# Clone the repository
git clone https://github.com/kumpeapps/mercury_bank_download.git
cd mercury_bank_download

# Update docker-compose.yml with your Docker Hub username
# Edit the image names in docker-compose.yml

# Start all services using published images
make prod-up

# View logs
make logs

# Access web interface at http://localhost:5001
# Access database admin at http://localhost:8080
```

### Option 2: Development Environment

Build and run locally for development:

```bash
# Clone the repository
git clone https://github.com/kumpeapps/mercury_bank_download.git
cd mercury_bank_download

# Start development environment (builds locally)
make dev

# View logs
make logs
```

### Option 3: Individual Service Deployment

Deploy services separately:

```bash
# Start only the sync service
cd sync_app
docker-compose up -d

# Or start only the web interface
cd web_app
docker-compose up -d
```

### Local Development with MySQL

For local development and testing, use the included MySQL database:

```bash
# Start all services with local MySQL
./dev.sh start

# Or start in development mode (with local builds and hot reload)
./dev.sh start-dev

# View logs
./dev.sh logs

# Access the applications:
# - Web Interface: http://localhost:5001
# - Database Admin (Adminer): http://localhost:8080
# - MySQL: localhost:3306
```

### Development Helper Script

The `dev.sh` script provides convenient commands for local development:

```bash
./dev.sh start          # Start all services
./dev.sh start-dev      # Start with development builds
./dev.sh stop           # Stop all services
./dev.sh logs           # View all logs
./dev.sh build          # Build local images
./dev.sh clean          # Clean up containers and volumes
./dev.sh migrate        # Run database migrations
./dev.sh encrypt-keys   # Encrypt existing API keys
./dev.sh test-encrypt   # Test encryption functionality
./dev.sh shell-sync     # Open shell in sync container
./dev.sh shell-web      # Open shell in web container
./dev.sh shell-db       # Open MySQL shell
```

### Database Configuration

**Local Development** (default):
- Database: `mysql://mercury_user:mercury_password@localhost:3306/mercury_db`
- MySQL runs in Docker container
- Data persisted in Docker volume `mysql_data`

**Production**:
- Configure `DATABASE_URL` in `docker-compose.yml`
- Update credentials and connection details as needed

## 📋 Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `MERCURY_API_KEY` | Mercury Bank API key | - | Single-account only |
| `MERCURY_API_URL` | Mercury API endpoint | `https://api.mercury.com` | No |
| `MERCURY_SANDBOX_MODE` | Use sandbox environment | `false` | No |
| `DATABASE_URL` | Complete database connection string | - | Yes |
| `SYNC_DAYS_BACK` | Days of transaction history to sync | `30` | No |
| `SYNC_INTERVAL_MINUTES` | Minutes between sync cycles | `60` | No |
| `RUN_ONCE` | Run once and exit | `false` | No |
| `MYSQL_ROOT_PASSWORD` | MySQL root password (Docker) | - | Docker only |
| `MYSQL_PASSWORD` | MySQL user password (Docker) | - | Docker only |

### Database Connection Examples

```bash
# Local MySQL
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/mercury_bank

# Remote MySQL
DATABASE_URL=mysql+pymysql://user:password@db.example.com:3306/mercury_bank

# Docker internal
DATABASE_URL=mysql+pymysql://mercury:password@db:3306/mercury_bank
```

## 🗄️ Database Schema

### Architecture Overview

The system uses a normalized relational schema supporting both single and multi-account deployments:

```
Users ←→ UserMercuryAccount ←→ MercuryAccounts
                                      ↓
                                  Accounts
                                      ↓
                                Transactions
```

### Core Tables

#### `users` - User Management
| Field | Type | Description |
|-------|------|-------------|
| `id` | VARCHAR(255) PK | Unique user identifier (UUID) |
| `username` | VARCHAR(100) UNIQUE | User login name |
| `email` | VARCHAR(255) UNIQUE | User email address |
| `password_hash` | VARCHAR(255) | Bcrypt hashed password |
| `first_name` | VARCHAR(100) | User's first name |
| `last_name` | VARCHAR(100) | User's last name |
| `is_active` | BOOLEAN | Account active status |
| `is_admin` | BOOLEAN | Administrative privileges |
| `last_login` | TIMESTAMP | Last login time |
| `created_at` | TIMESTAMP | Record creation time |
| `updated_at` | TIMESTAMP | Last update time |

#### `mercury_accounts` - Account Groups
| Field | Type | Description |
|-------|------|-------------|
| `id` | VARCHAR(255) PK | Account group identifier (UUID) |
| `name` | VARCHAR(255) | Display name for account group |
| `api_key` | VARCHAR(500) | Mercury Bank API key |
| `sandbox_mode` | BOOLEAN | Sandbox/production mode |
| `description` | TEXT | Optional description |
| `is_active` | BOOLEAN | Active status |
| `sync_enabled` | BOOLEAN | Sync enabled for this group |
| `last_sync_at` | TIMESTAMP | Last successful sync |
| `created_at` | TIMESTAMP | Record creation time |
| `updated_at` | TIMESTAMP | Last update time |

#### `accounts` - Mercury Bank Accounts
| Field | Type | Description |
|-------|------|-------------|
| `id` | VARCHAR(255) PK | Mercury account ID |
| `mercury_account_id` | VARCHAR(255) FK | Reference to mercury_accounts |
| `name` | VARCHAR(255) | Account name |
| `account_number` | VARCHAR(50) UNIQUE | Bank account number |
| `routing_number` | VARCHAR(20) | Bank routing number |
| `account_type` | VARCHAR(50) | Account type (checking, savings, etc.) |
| `status` | VARCHAR(50) | Account status |
| `balance` | DECIMAL(15,2) | Current balance |
| `available_balance` | DECIMAL(15,2) | Available balance |
| `currency` | VARCHAR(3) | Currency code (USD) |
| `is_active` | BOOLEAN | Account active status |
| `created_at` | TIMESTAMP | Record creation time |
| `updated_at` | TIMESTAMP | Last update time |

#### `transactions` - Financial Transactions
| Field | Type | Description |
|-------|------|-------------|
| `id` | VARCHAR(255) PK | Mercury transaction ID |
| `account_id` | VARCHAR(255) FK | Reference to accounts |
| `amount` | DECIMAL(15,2) | Transaction amount |
| `currency` | VARCHAR(3) | Currency code |
| `description` | TEXT | Transaction description |
| `transaction_type` | VARCHAR(20) | Type (debit/credit) |
| `status` | VARCHAR(50) | Transaction status |
| `category` | VARCHAR(100) | Transaction category |
| `counterparty_name` | VARCHAR(255) | Other party name |
| `counterparty_account` | VARCHAR(255) | Other party account |
| `reference_number` | VARCHAR(100) | Reference number |
| `posted_at` | TIMESTAMP | Transaction post time |
| `created_at` | TIMESTAMP | Record creation time |
| `updated_at` | TIMESTAMP | Last update time |

#### `user_mercury_account_association` - Access Control
| Field | Type | Description |
|-------|------|-------------|
| `user_id` | VARCHAR(255) FK | Reference to users |
| `mercury_account_id` | VARCHAR(255) FK | Reference to mercury_accounts |

## 🔧 Usage Examples

### Basic Operations

```bash
# Run sync once and exit
echo "RUN_ONCE=true" >> .env
docker-compose up mercury-sync

# Continuous sync (default)
docker-compose up -d

# Sync every 15 minutes
echo "SYNC_INTERVAL_MINUTES=15" >> .env
docker-compose restart mercury-sync

# Sync last 7 days only
echo "SYNC_DAYS_BACK=7" >> .env
docker-compose restart mercury-sync

# Enable sandbox mode
echo "MERCURY_SANDBOX_MODE=true" >> .env
docker-compose restart mercury-sync
```

### Monitoring & Troubleshooting

```bash
# View real-time logs
docker-compose logs -f mercury-sync

# Check service status
docker-compose ps

# View last 100 log lines
docker-compose logs --tail=100 mercury-sync

# Access database
docker-compose exec db mysql -u mercury -p mercury_bank

# Check container health
docker-compose exec mercury-sync python health_check.py

# Complete reset (⚠️ Destroys all data)
docker-compose down -v
docker-compose up --build -d
```

### Database Operations

```bash
# Connect to MySQL
docker-compose exec db mysql -u mercury -p

# Backup database
docker-compose exec db mysqldump -u mercury -p mercury_bank > backup.sql

# Restore database
docker-compose exec -T db mysql -u mercury -p mercury_bank < backup.sql

# View sync status
docker-compose exec db mysql -u mercury -p -e "
SELECT 
    ma.name,
    ma.last_sync_at,
    ma.sync_enabled,
    COUNT(a.id) as account_count
FROM mercury_accounts ma
LEFT JOIN accounts a ON ma.id = a.mercury_account_id
GROUP BY ma.id;"
```

### Applying Changes Properly

When making changes to the application, it's crucial to follow the correct procedure to ensure all components are properly rebuilt and synchronized:

```bash
# ALWAYS use this command to apply changes:
./dev.sh rebuild-dev
```

This command will:

1. Stop all running containers
2. Rebuild the Docker images with your latest code changes
3. Start all services in development mode
4. Run migrations automatically

❌ **NEVER** use these commands for applying changes:

- `docker restart container-name`
- `docker-compose restart`

Using direct Docker commands may lead to inconsistencies between the code and running containers, migration issues, and other hard-to-debug problems.

You can use the provided helper script to apply changes properly:

```bash
./apply-changes.sh
```

## 🐳 Docker Deployment

### Available Images

- **Production**: `kumpeapps/mercury_bank_download:latest`
- **Beta**: `mercury_bank_download:latest-beta`

### Custom Docker Build

```bash
# Standard build
docker build -t mercury-sync .

# Ubuntu-based build
docker build -f Dockerfile.ubuntu -t mercury-sync:ubuntu .

# Multi-architecture build
docker buildx build --platform linux/amd64,linux/arm64 -t mercury-sync .
```

### Docker Compose Configurations

**Development:**
```yaml
version: '3.8'
services:
  mercury-sync:
    build: .
    environment:
      - DATABASE_URL=mysql+pymysql://mercury:password@db:3306/mercury_bank
      - MERCURY_API_KEY=${MERCURY_API_KEY}
      - SYNC_INTERVAL_MINUTES=5
    volumes:
      - ./logs:/app/logs
```

**Production:**
```yaml
version: '3.8'
services:
  mercury-sync:
    image: kumpeapps/mercury_bank_download:latest
    environment:
      - DATABASE_URL=mysql+pymysql://user:pass@external-db:3306/mercury
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "health_check.py"]
      interval: 30s
      timeout: 10s
      retries: 3
```

## 💻 Development

### Local Development Setup

```bash
# Clone repository
git clone https://github.com/kumpeapps/mercury_bank_download.git
cd mercury_bank_download

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your settings

# Initialize database
python setup_db.py

# Run sync
python sync.py
```

### Project Structure

```
mercury_bank_download/
├── sync_app/                    # Mercury Bank sync service
│   ├── models/                  # Database models
│   ├── migrations/              # Database migrations
│   ├── sync.py                  # Main sync application
│   ├── migration_manager.py     # Migration management
│   ├── Dockerfile              # Sync service container
│   ├── docker-compose.yml      # Sync service compose
│   ├── requirements.txt        # Python dependencies
│   └── README.md               # Sync service documentation
├── web_app/                     # Web interface
│   ├── models/                  # Database models (shared schema)
│   ├── migrations/              # Web app migrations
│   ├── templates/               # HTML templates
│   ├── app.py                   # Flask web application
│   ├── Dockerfile              # Web app container
│   ├── docker-compose.yml      # Web app compose
│   ├── requirements.txt        # Python dependencies
│   └── README.md               # Web app documentation
├── docker-compose.yml          # Main orchestration file
└── README.md                   # This file
```

### Testing

```bash
# Run with sandbox mode
MERCURY_SANDBOX_MODE=true python sync.py

# Test with minimal data
SYNC_DAYS_BACK=1 RUN_ONCE=true python sync.py

# Run health check
python health_check.py

# Lint code
flake8 .
black --check .

# Run tests (if available)
pytest
```

### Migration from Single to Multi-Account

```bash
# 1. Backup existing data
docker-compose exec db mysqldump -u mercury -p mercury_bank > backup.sql

# 2. Run migration
mysql -u mercury -p mercury_bank < migration.sql

# 3. Set up multi-account structure
python setup_db.py

# 4. Update configuration
cp docker-compose-example.yml docker-compose.yml
# Edit DATABASE_URL and remove MERCURY_API_KEY

# 5. Restart services
docker-compose down
docker-compose up -d
```

## 🔍 Troubleshooting

### Common Issues

| Issue | Symptoms | Solution |
|-------|----------|----------|
| **Invalid API Key** | `401 Unauthorized` errors | Verify API key in Mercury dashboard |
| **Database Connection** | `Connection refused` errors | Check DATABASE_URL and database status |
| **Sync Failures** | Missing transactions | Check Mercury API rate limits |
| **Container Issues** | Service won't start | Review `docker-compose logs` |
| **Permission Errors** | User access denied | Verify user-account associations |

### Debugging Commands

```bash
# Check API connectivity
curl -H "Authorization: Bearer $MERCURY_API_KEY" https://api.mercury.com/api/v1/accounts

# Test database connection
docker-compose exec mercury-sync python -c "
from models.base import create_engine_and_session
engine, session = create_engine_and_session()
print('Database connection successful')
"

# Validate configuration
docker-compose exec mercury-sync python -c "
import os
print('API Key:', os.getenv('MERCURY_API_KEY', 'Not set'))
print('Database URL:', os.getenv('DATABASE_URL', 'Not set'))
"
```

### Log Analysis

```bash
# Error patterns
docker-compose logs mercury-sync | grep ERROR

# Sync statistics
docker-compose logs mercury-sync | grep "Sync completed"

# API rate limit warnings
docker-compose logs mercury-sync | grep "rate limit"

# Database errors
docker-compose logs mercury-sync | grep "SQLAlchemy"
```

## 🆕 What's New

### Version 2.0+ Features

- ✅ **Multi-Account Architecture** - Manage multiple Mercury Bank accounts
- ✅ **User Management System** - Role-based access control
- ✅ **Sandbox Environment** - Built-in testing support
- ✅ **Enhanced Docker Support** - Multiple image variants
- ✅ **Improved Error Handling** - Better resilience and recovery
- ✅ **Health Monitoring** - Comprehensive status reporting
- ✅ **Migration Tools** - Easy upgrade from v1.x

### Roadmap

- 🔄 **Real-time Webhooks** - Instant transaction notifications
- 📊 **Analytics Dashboard** - Transaction insights and reporting
- 🔐 **Enhanced Security** - OAuth2 and API key rotation
- 📱 **Mobile API** - REST API for mobile applications
- 🚀 **Performance Optimization** - Parallel sync processing

## 🤝 Contributing

We welcome contributions! Please read our contributing guidelines:

### Development Workflow

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

### Testing Requirements

- ✅ Test single-account mode
- ✅ Test multi-account mode
- ✅ Test sandbox environment
- ✅ Test Docker deployment
- ✅ Update documentation
- ✅ Follow code style guidelines

### Code Standards

```bash
# Format code
black .

# Lint code
flake8 .

# Type checking
mypy .
```

## 📚 Documentation

- 📖 **[Multi-Account Setup Guide](MULTI_ACCOUNT_README.md)** - Comprehensive multi-account configuration
- 🐳 **[Docker Troubleshooting](DOCKER_TROUBLESHOOTING.md)** - Docker-specific issues and solutions
- 🏦 **[Mercury Bank API Docs](https://mercury.com/developers)** - Official API documentation

## ⚖️ License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/kumpeapps/mercury_bank_download/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/kumpeapps/mercury_bank_download/discussions)
- 📧 **Email**: support@kumpeapps.com

---

**Made with ❤️ for the Mercury Bank community**
