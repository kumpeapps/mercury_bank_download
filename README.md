# Mercury Bank Integration Platform

[![Docker Hub - Sync Service](https://img.shields.io/docker/v/justinkumpe/mercury-bank-sync?sort=semver&label=sync%20service&logo=docker&logoColor=white)](https://hub.docker.com/r/justinkumpe/mercury-bank-sync)
[![Docker Hub - Web GUI](https://img.shields.io/docker/v/justinkumpe/mercury-bank-sync-gui?sort=semver&label=web%20gui&logo=docker&logoColor=white)](https://hub.docker.com/r/justinkumpe/mercury-bank-sync-gui)
[![Docker Stars - Sync](https://img.shields.io/docker/stars/justinkumpe/mercury-bank-sync?logo=docker&logoColor=white&label=sync%20stars)](https://hub.docker.com/r/justinkumpe/mercury-bank-sync)
[![Docker Stars - GUI](https://img.shields.io/docker/stars/justinkumpe/mercury-bank-sync-gui?logo=docker&logoColor=white&label=gui%20stars)](https://hub.docker.com/r/justinkumpe/mercury-bank-sync-gui)

A comprehensive platform for Mercury Bank data synchronization and management, consisting of two main components:

1. **Sync Service** (`sync_app/`) - Automated data synchronization from Mercury Bank API
2. **Web Interface** (`web_app/`) - User-friendly web dashboard for data management and reporting

## 🎉 What's New in v2.1.0

### 🏦 Complete Budget Management System
Mercury Bank Integration Platform now includes comprehensive budget management capabilities:

- **Budget Creation & Editing** - Create monthly budgets with category-based spending limits
- **Real-Time Progress Tracking** - Color-coded status indicators (green/yellow/red) based on spending progress
- **Advanced Budget Reports** - Interactive reports with variance analysis and transaction drill-down
- **Multi-Account Support** - Create budgets spanning multiple Mercury accounts within a group
- **Smart Analytics Integration** - Visual budget vs. actual spending charts in reports dashboard
- **Role-Based Access Control** - Budget management restricted to users with appropriate permissions
- **Easy Month-to-Month Planning** - One-click budget copying for future months

**See the [Budget Management](#budget-management) section below for detailed usage instructions.**

### Previous Updates

#### v2.0.1
- **Enhanced Chart Controls** - Reports now show main categories by default with toggle for sub-categories
- **Improved User Experience** - Cleaner, simplified chart views with drill-down capability
- **Dynamic Chart Updates** - One-click toggle between category and sub-category views

#### v2.0.0
- **Mercury Account User Management** - Add/remove user access to Mercury accounts through CLI
- **Enhanced CLI Interface** - Improved command-line interface with additional management features
- **Comprehensive Testing** - Complete test suite with 38 test cases
- **Security Improvements** - Strengthened role-based access control
- **Documentation Updates** - Complete CLI documentation and improved README

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
- 📈 **Reporting & Analytics** - Interactive charts with category/sub-category toggle, trends, and financial insights
- 🎯 **Default Account Settings** - User-customizable default views
- 📱 **Responsive Design** - Works on desktop, tablet, and mobile devices
- 🏦 **Budget Management** - Complete budgeting system (see [Budget Management](#budget-management) for details)

## 🚀 Quick Start

### Prerequisites

- **Docker & Docker Compose** (recommended)
- **Mercury Bank API Key** ([Get yours here](https://mercury.com/developers))
- **Database Server** - MySQL, PostgreSQL, or other SQLAlchemy-supported database

### Access Methods

- **Web Interface**: Access via browser at http://localhost:5001 (default)
- **CLI Interface**: Access via `./dev.sh cli-gui` or `docker-compose exec mercury-sync python cli_gui.py`
- **Database Admin**: Access via browser at http://localhost:8080 (default)

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

#### `budgets` - Budget Management
| Field | Type | Description |
|-------|------|-------------|
| `id` | INTEGER PK | Unique budget identifier |
| `name` | VARCHAR(255) | Budget display name |
| `mercury_account_id` | INTEGER FK | Reference to mercury_accounts |
| `budget_month` | DATE | Budget month (YYYY-MM-01 format) |
| `is_active` | BOOLEAN | Budget active status |
| `created_by_user_id` | INTEGER FK | Reference to users (budget creator) |
| `created_at` | TIMESTAMP | Record creation time |
| `updated_at` | TIMESTAMP | Last update time |

#### `budget_categories` - Budget Category Limits
| Field | Type | Description |
|-------|------|-------------|
| `id` | INTEGER PK | Unique budget category identifier |
| `budget_id` | INTEGER FK | Reference to budgets |
| `category_name` | VARCHAR(255) | Transaction category name |
| `budgeted_amount` | FLOAT | Allocated budget amount for category |
| `is_active` | BOOLEAN | Category active status |
| `created_at` | TIMESTAMP | Record creation time |
| `updated_at` | TIMESTAMP | Last update time |

#### `budget_accounts` - Budget Account Associations
| Field | Type | Description |
|-------|------|-------------|
| `budget_id` | INTEGER FK | Reference to budgets |
| `account_id` | VARCHAR(255) FK | Reference to accounts |
| `created_at` | TIMESTAMP | Association creation time |

## 🧪 Testing

The platform includes a comprehensive test suite to ensure reliability and correct functionality:

### Running Tests

```bash
# Run all tests with coverage report
./run_tests.sh

# Run tests without coverage
./run_tests.sh --no-coverage

# Run specific test patterns
./run_tests.sh --pattern="test_user_*"

# Run with verbose output
./run_tests.sh --verbose
```

### Test Categories

The test suite covers three main areas:

#### Model Tests (17 test cases)
- User model creation and password handling
- Role-based permissions and relationships
- User settings and system settings
- Mercury account and transaction relationships

#### User Registration Tests (9 test cases)
- First user automatically receives admin roles
- Subsequent users get only user role
- Password hashing and validation
- Username uniqueness enforcement

#### Web Integration Tests (12 test cases)
- Registration workflow and form processing
- Authentication flow (login/logout)
- Permission enforcement for protected routes
- System settings and error handling

### Key Validations
- Role assignment logic works correctly
- Authentication security is properly implemented
- Permission system follows role-based access control
- Database integrity is maintained
- Error handling follows best practices

## 🖥️ Command-Line Interface

The platform includes a powerful command-line interface (CLI) for system management without requiring the web interface:

### Accessing the CLI

```bash
# Using the development helper script (recommended)
./dev.sh cli-gui

# Direct Docker execution
docker-compose exec mercury-sync python cli_gui.py

# Using the standalone launcher
./sync_app/launch_cli.sh
```

### CLI Features

The CLI provides comprehensive system management capabilities:

- **System Status** - Database connection, user counts, configuration overview
- **Mercury Account Management** - Add, edit, enable/disable Mercury accounts
- **User Management** - Create users, manage roles, reset passwords
- **Sync Activity** - View transactions, check sync status, monitor logs
- **Database Tools** - Run migrations, check schema, view statistics

### Mercury Account User Management

The CLI supports complete user access management for Mercury accounts:

- View which users have access to Mercury accounts
- Add user access to Mercury accounts
- Remove user access from Mercury accounts
- Enforce security by preventing inaccessible accounts

For complete CLI documentation, see [CLI_GUI_DOCUMENTATION.md](CLI_GUI_DOCUMENTATION.md).

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

### Database Migrations with Alembic

This project uses [Alembic](https://alembic.sqlalchemy.org/) for database schema migrations. Alembic provides database-agnostic migration support for any database supported by SQLAlchemy.

#### Quick Migration Commands

```bash
# Check current migration status
python migrate.py status

# Apply all pending migrations
python migrate.py upgrade

# Create a new migration for model changes
python migrate.py autogenerate -m "Add new feature"

# Test database connection
python migrate.py test-connection
```

#### Docker Environment Migrations

In Docker environments, migrations run automatically during container startup. For manual migration management:

```bash
# Run migrations in web container
docker-compose exec web-app python migrate.py upgrade

# Check migration status
docker-compose exec web-app python migrate.py status

# Create new migration
docker-compose exec web-app python migrate.py autogenerate -m "Description"
```

For detailed migration documentation, see [docs/ALEMBIC_MIGRATION_GUIDE.md](docs/ALEMBIC_MIGRATION_GUIDE.md).

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

- **Production**: `justinkumpe/mercury-bank-sync:latest`
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
      - SYNC_INTERVAL_MINUTES=5
    volumes:
      - ./logs:/app/logs
```

**Production:**
```yaml
version: '3.8'
services:
  mercury-sync:
    image: justinkumpe/mercury-bank-sync:latest
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

The platform includes a comprehensive test suite to ensure reliability and maintainability:

```bash
# Run all tests with coverage
./run_tests.sh

# Run tests without coverage reporting
./run_tests.sh --no-coverage

# Run tests in verbose mode
./run_tests.sh --verbose

# Run specific test patterns
./run_tests.sh --pattern="test_user*"

# Run individual test categories
python -m pytest tests/test_models.py          # Model tests
python -m pytest tests/test_user_registration.py  # Registration tests
python -m pytest tests/test_web_integration.py    # Web integration tests
```

#### Test Coverage
- **38 test cases** covering critical functionality
- **Model Tests** (17 tests) - Database models and relationships
- **User Registration** (9 tests) - Role assignment and authentication
- **Web Integration** (12 tests) - HTTP endpoints and user workflows

#### Test Features
- ✅ **Role Assignment Logic** - First user gets admin roles, others get user role
- ✅ **Authentication Security** - Password hashing and session management
- ✅ **Web Interface Testing** - Registration, login, and protected routes
- ✅ **Database Validation** - Model relationships and constraints
- ✅ **Error Handling** - Edge cases and validation scenarios
- ✅ **CI/CD Integration** - Automated testing in GitHub Actions

#### Development Testing
```bash
# Test sync service functionality
MERCURY_SANDBOX_MODE=true python sync.py

# Test with minimal data
SYNC_DAYS_BACK=1 RUN_ONCE=true python sync.py

# Run health checks
python health_check.py

# Code quality checks
flake8 .
black --check .
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
# Edit DATABASE_URL and configure Mercury accounts via web interface

# 5. Restart services
docker-compose down
docker-compose up -d
```

## 🔄 Database Migrations

### Budget System Database Migrations

The budget management system was introduced in v2.1.0 with comprehensive database schema changes. The migration system uses **Alembic** to manage these changes automatically.

#### Migration Files

**Primary Migration**: `b5ed68a6aa24_add_budgets_and_budget_categories_.py`
- **Created**: 2025-07-06 15:29:27
- **Revision ID**: `b5ed68a6aa24`
- **Previous Revision**: `11064205e552`

#### Tables Created

1. **`budgets`** - Main budget records
   - Primary key: `id` (INTEGER, AUTO_INCREMENT)
   - Foreign keys: `mercury_account_id` → `mercury_accounts.id`, `created_by_user_id` → `users.id`
   - Indexes: Automatic indexes on foreign key columns

2. **`budget_categories`** - Budget category spending limits
   - Primary key: `id` (INTEGER, AUTO_INCREMENT) 
   - Foreign key: `budget_id` → `budgets.id`
   - Cascade delete: Categories are removed when budget is deleted

3. **`budget_accounts`** - Many-to-many budget-account associations
   - Composite primary key: `(budget_id, account_id)`
   - Foreign keys: `budget_id` → `budgets.id`, `account_id` → `accounts.id`

#### Migration Commands

```bash
# Check current migration status
docker-compose exec web-app python migrate.py status
docker-compose exec sync-app python migrate.py status

# Apply budget system migrations (automatic on container startup)
docker-compose exec web-app python migrate.py upgrade
docker-compose exec sync-app python migrate.py upgrade

# View migration history including budget changes
docker-compose exec web-app python migrate.py history --verbose
```

#### Migration Safety

- **Backward Compatible**: The migration includes proper `downgrade()` functions
- **Foreign Key Constraints**: Proper referential integrity maintained
- **Rollback Support**: Can safely rollback budget tables if needed
- **Data Preservation**: Existing transaction and user data remains untouched

#### Post-Migration Setup

After the budget migration runs, the following role is automatically created:
- **`budgets`** role - Required for budget management access

**Role Assignment**:
```bash
# Assign budget role to admin users (via CLI or web interface)
./dev.sh cli-gui
# Select: User Management → Assign Role → Select User → Add "budgets" role
```

#### Troubleshooting Migrations

```bash
# If migration fails, check current database state
docker-compose exec db mysql -u mercury -p -e "SHOW TABLES LIKE '%budget%';"

# View migration table status
docker-compose exec db mysql -u mercury -p -e "SELECT * FROM alembic_version;"

# Force migration to specific revision (use with caution)
docker-compose exec web-app python migrate.py stamp b5ed68a6aa24
```

**Important**: Budget migrations run automatically when containers start. Manual intervention is typically only needed for troubleshooting or custom deployments.

## 🆕 What's New

### Version 2.1.0 Features

- ✅ **Complete Budget Management System** - See [Budget Management](#budget-management) section for full details
- ✅ **Multi-Account Architecture** - Manage multiple Mercury Bank accounts
- ✅ **User Management System** - Role-based access control
- ✅ **Analytics Dashboard** - Interactive transaction insights with integrated budget analytics
- ✅ **Enhanced Chart Controls** - Dynamic category/sub-category toggle views

### Previous Version Features

- ✅ **Sandbox Environment** - Built-in testing support
- ✅ **Enhanced Docker Support** - Multiple image variants
- ✅ **Improved Error Handling** - Better resilience and recovery
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
