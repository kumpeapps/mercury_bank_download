# Migration Guide

This guide helps you migrate from single-account to multi-account mode, or set up a fresh multi-account installation.

## 🎯 Overview

The multi-account system provides:
- **Multiple Mercury Bank accounts** with different API keys
- **User management** with authentication and permissions
- **Flexible access control** where users can access multiple account groups
- **Centralized configuration** stored in the database

## 🚀 Quick Migration (Existing Single-Account Setup)

### Step 1: Backup Your Data
```bash
# Backup your existing database
docker-compose exec db mysqldump -u mercury -p mercury_bank > backup_$(date +%Y%m%d_%H%M%S).sql
```

### Step 2: Run Migration Script
```bash
# Apply the migration
mysql -u mercury -p mercury_bank < migration.sql
```

### Step 3: Verify Migration
```bash
# Verify the migration was successful
python verify_migration.py
```

### Step 4: Set Up Initial Data
```bash
# Set up Mercury accounts and users
python setup_db.py
```

### Step 5: Update Configuration
```bash
# Remove single-account environment variable
# Edit your .env file and remove/comment out:
# MERCURY_API_KEY=your_key_here

# Or update docker-compose.yml to remove MERCURY_API_KEY
# and ensure DATABASE_URL points to your database
```

### Step 6: Restart Services
```bash
# Restart the sync service
docker-compose restart mercury-sync

# Check logs
docker-compose logs -f mercury-sync
```

## 🆕 Fresh Multi-Account Installation

### Step 1: Set Up Database
```bash
# Initialize the database with multi-account support
python setup_db.py
```

### Step 2: Use Multi-Account Configuration
```bash
# Use the example configuration
cp docker-compose-example.yml docker-compose.yml

# Edit DATABASE_URL to point to your database
nano docker-compose.yml
```

### Step 3: Start Services
```bash
docker-compose up -d
```

## 🔧 Migration Scripts Reference

### Available Scripts

| Script | Purpose | Usage |
|--------|---------|-------|
| `migration.sql` | Adds multi-account tables to existing database | `mysql < migration.sql` |
| `rollback_migration.sql` | Reverts to single-account mode | `mysql < rollback_migration.sql` |
| `setup_db.py` | Interactive database setup | `python setup_db.py` |
| `verify_migration.py` | Verifies migration success | `python verify_migration.py` |

### Migration Script Details

#### `migration.sql`
- Creates `users`, `mercury_accounts`, and `user_mercury_accounts` tables
- Adds `mercury_account_id` column to existing `accounts` table
- Creates performance indexes
- Includes optional sample data creation
- Safe to run multiple times (uses IF NOT EXISTS)

#### `rollback_migration.sql`
- ⚠️ **WARNING**: Deletes all multi-account data
- Removes multi-account tables and columns
- Reverts database to single-account structure
- Use only if you need to go back to single-account mode

#### `setup_db.py`
- Interactive setup for Mercury accounts and users
- Supports both sample and production data creation
- Handles password hashing securely
- Validates data integrity

#### `verify_migration.py`
- Checks all required tables and columns exist
- Verifies foreign key constraints
- Checks performance indexes
- Reports data integrity issues
- Provides troubleshooting guidance

## 🔐 Security Considerations

### Password Management
```bash
# Generate secure password hash (Python)
python -c "
import bcrypt
password = input('Enter password: ')
hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
print(f'Hash: {hash}')
"
```

### API Key Security
- API keys are stored in the database (not environment variables)
- Consider encrypting API keys at rest for production
- Use different API keys for different environments
- Rotate API keys regularly

### Database Security
- Use strong passwords for database users
- Limit database access to necessary hosts only
- Enable SSL/TLS for database connections
- Regular security updates

## 🚨 Troubleshooting

### Common Issues

#### Migration Fails with Foreign Key Errors
```bash
# Check if tables exist
mysql -u mercury -p -e "SHOW TABLES" mercury_bank

# Check existing foreign keys
mysql -u mercury -p -e "
SELECT * FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
WHERE TABLE_SCHEMA = 'mercury_bank' 
AND REFERENCED_TABLE_NAME IS NOT NULL
" mercury_bank
```

#### Existing Data Migration
```bash
# If you have existing accounts, link them to a Mercury account group
mysql -u mercury -p mercury_bank -e "
-- Create a default Mercury account group
INSERT INTO mercury_accounts (name, api_key, sandbox_mode, description)
VALUES ('Default Account', 'your_existing_api_key', FALSE, 'Migrated from single-account setup');

-- Link all existing accounts to this group
UPDATE accounts SET mercury_account_id = LAST_INSERT_ID() WHERE mercury_account_id IS NULL;
"
```

#### Permission Issues
```bash
# Grant necessary permissions
mysql -u root -p -e "
GRANT ALL PRIVILEGES ON mercury_bank.* TO 'mercury'@'%';
FLUSH PRIVILEGES;
"
```

#### Sync Service Issues
```bash
# Check if multi-account mode is working
docker-compose logs mercury-sync | grep -i "mercury account"

# Verify API keys in database
mysql -u mercury -p mercury_bank -e "
SELECT id, name, LEFT(api_key, 10) as api_key_preview, sandbox_mode, is_active, sync_enabled 
FROM mercury_accounts
"
```

### Recovery Procedures

#### Restore from Backup
```bash
# Stop services
docker-compose down

# Restore database
mysql -u mercury -p mercury_bank < backup_YYYYMMDD_HHMMSS.sql

# Restart services
docker-compose up -d
```

#### Reset Multi-Account Setup
```bash
# Run rollback script
mysql -u mercury -p mercury_bank < rollback_migration.sql

# Run migration again
mysql -u mercury -p mercury_bank < migration.sql

# Set up data again
python setup_db.py
```

## ✅ Verification Checklist

After migration, verify:

- [ ] All required tables exist (`users`, `mercury_accounts`, `user_mercury_accounts`)
- [ ] Foreign key relationships are properly set up
- [ ] Existing accounts are linked to Mercury account groups
- [ ] At least one user with admin privileges exists
- [ ] API keys are correctly stored in `mercury_accounts` table
- [ ] Sync service starts without errors
- [ ] New transactions are being synced
- [ ] User permissions work as expected

## 📞 Getting Help

If you encounter issues:

1. **Check logs**: `docker-compose logs mercury-sync`
2. **Run verification**: `python verify_migration.py`
3. **Review documentation**: [MULTI_ACCOUNT_README.md](MULTI_ACCOUNT_README.md)
4. **Check Docker issues**: [DOCKER_TROUBLESHOOTING.md](DOCKER_TROUBLESHOOTING.md)
5. **Report bugs**: GitHub Issues

## 🔄 Migration Rollback

If you need to revert to single-account mode:

⚠️ **WARNING**: This will delete all multi-account data!

```bash
# Backup first
mysqldump -u mercury -p mercury_bank > backup_before_rollback.sql

# Run rollback
mysql -u mercury -p mercury_bank < rollback_migration.sql

# Restore single-account configuration
# Add MERCURY_API_KEY back to your .env or docker-compose.yml

# Restart services
docker-compose restart mercury-sync
```
