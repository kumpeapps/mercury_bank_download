# Database Migration System

This directory contains the automatic database migration system for the Mercury Bank application.

## Overview

The migration system automatically runs database schema changes when the Docker containers start, ensuring your database is always up to date with the latest schema requirements. 

**Key Features:**
- **Database Agnostic**: Uses SQLAlchemy for compatibility with MySQL, PostgreSQL, SQLite, and more
- **Universal Support**: Works with any SQLAlchemy-supported database without modification
- **Backward Compatible**: Supports older MySQL/MariaDB versions by using TEXT instead of JSON columns

## How It Works

1. **Automatic Execution**: Migrations run automatically when containers start
2. **Tracking**: Each migration is tracked in a `migrations` table to prevent re-execution
3. **Validation**: Migration files are checksummed to detect unauthorized changes
4. **Sequential**: Migrations run in alphabetical order by filename

## Migration Files

Migration files are stored in the `migrations/` directory and follow this naming convention:
```
NNN_description.sql
```

Where:
- `NNN` is a zero-padded sequence number (001, 002, etc.)
- `description` is a brief description of the migration
- `.sql` extension indicates it's a SQL migration file

### Example Migration File

**001_add_user_settings_table.sql**
```sql
-- Migration: 001_add_user_settings_table.sql
-- Description: Add user_settings table for storing user preferences

CREATE TABLE user_settings (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL UNIQUE,
    primary_mercury_account_id INT NULL,
    -- ... more columns
);

-- Add indexes
CREATE INDEX idx_user_settings_user_id ON user_settings(user_id);
```

## Current Migrations

### 001_add_user_settings_table.sql
- **Purpose**: Creates the `user_settings` table for storing user preferences
- **Features**:
  - Primary Mercury account selection
  - JSON fields for flexible preference storage
  - Foreign key constraints with proper cascading
  - Performance indexes

## Usage

### Automatic (Recommended)
Migrations run automatically when you start the Docker containers:

```bash
docker-compose up -d
```

### Manual Testing
You can test the migration system manually:

```bash
# Test migration system
python test_migrations.py

# Run migrations manually
python migration_manager.py
```

### Creating New Migrations

1. Create a new `.sql` file in the `migrations/` directory
2. Use the next sequential number: `002_your_description.sql`
3. Include a comment header describing the migration
4. Write your SQL statements
5. Test locally before deploying

**Example:**
```sql
-- Migration: 002_add_audit_table.sql
-- Description: Add audit logging table for tracking user actions

CREATE TABLE audit_log (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    action VARCHAR(100) NOT NULL,
    details JSON NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX idx_audit_log_user_id ON audit_log(user_id);
CREATE INDEX idx_audit_log_created_at ON audit_log(created_at);
```

## Database Schema Tracking

The migration system creates a `migrations` table to track executed migrations:

| Column | Type | Description |
|--------|------|-------------|
| id | INT | Primary key |
| filename | VARCHAR(255) | Migration filename |
| checksum | VARCHAR(64) | MD5 hash of file content |
| executed_at | TIMESTAMP | When migration was executed |

## Safety Features

1. **Checksum Validation**: Detects if migration files are modified after execution
2. **Transaction Safety**: Each migration runs in a transaction (where possible)
3. **Error Handling**: Detailed error logging and graceful failure handling
4. **Idempotent**: Safe to run multiple times - already executed migrations are skipped

## Troubleshooting

### Migration Fails to Execute
1. Check the application logs for detailed error messages
2. Verify database connectivity
3. Ensure migration SQL syntax is correct
4. Check database permissions

### Migration File Modified Error
If you see a "migration file modified" error:
1. **DO NOT** modify executed migration files
2. Create a new migration file to make additional changes
3. If absolutely necessary, manually update the checksum in the database

### Reset Migrations (Development Only)
**⚠️ WARNING: This will lose all data!**

```sql
-- Drop migrations table to reset tracking
DROP TABLE IF EXISTS migrations;

-- Drop and recreate database
DROP DATABASE mercury_bank;
CREATE DATABASE mercury_bank;
```

## Best Practices

1. **Never modify executed migrations** - create new ones instead
2. **Test migrations locally** before deploying
3. **Keep migrations small and focused** - one logical change per migration
4. **Include rollback instructions** in comments (for manual rollback if needed)
5. **Use descriptive filenames** - make it clear what the migration does
6. **Include proper indexes** for performance
7. **Use appropriate foreign key constraints** with cascading rules

## Integration with Docker

The migration system is integrated into the Docker startup process:

1. **Web App Container**: Runs migrations before starting Flask
2. **Sync Container**: Runs migrations before starting sync process
3. **Database Ready Check**: Waits for database to be available
4. **Failure Handling**: Container exits if migrations fail

This ensures your application always has the correct database schema when it starts.
