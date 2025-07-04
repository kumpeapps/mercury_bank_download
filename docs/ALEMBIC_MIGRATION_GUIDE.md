# Database Migrations with Alembic

This project uses [Alembic](https://alembic.sqlalchemy.org/) for database schema migrations. Alembic is database-agnostic and works with any database supported by SQLAlchemy.

## Setup

Alembic is already configured and initialized in this project. The configuration files are:

- `alembic.ini` - Main Alembic configuration
- `alembic/env.py` - Environment configuration that reads from DATABASE_URL
- `alembic/versions/` - Directory containing all migration files

## Environment Configuration

Alembic reads the database connection from the `DATABASE_URL` environment variable, which should be in the format:

```bash
DATABASE_URL=dialect+driver://username:password@host:port/database_name
```

Examples:

- MySQL: `mysql+pymysql://user:pass@localhost:3306/mercury_bank`
- PostgreSQL: `postgresql://user:pass@localhost:5432/mercury_bank`
- SQLite: `sqlite:///path/to/database.db`

## Migration Helper Script

Use the `migrate.py` helper script for common migration tasks:

```bash
# Check database connection
python migrate.py test-connection

# Check current migration status
python migrate.py status

# View migration history
python migrate.py history

# Upgrade to latest migration
python migrate.py upgrade

# Create a new empty migration
python migrate.py create -m "Add new feature"

# Auto-generate migration from model changes
python migrate.py autogenerate -m "Update user model"

# Downgrade to specific revision
python migrate.py downgrade -r revision_id

# Mark database as being at specific revision (without running migrations)
python migrate.py stamp -r revision_id
```

## Direct Alembic Commands

You can also use Alembic commands directly:

```bash
# Check current revision
alembic current

# Show migration history
alembic history

# Upgrade to latest
alembic upgrade head

# Downgrade one revision
alembic downgrade -1

# Create new migration
alembic revision -m "Description"

# Auto-generate migration
alembic revision --autogenerate -m "Description"
```

## Workflow

### 1. Making Model Changes

When you modify SQLAlchemy models in `web_app/models/` or `sync_app/models/`, create a migration:

```bash
python migrate.py autogenerate -m "Update user model with new field"
```

### 2. Review the Migration

Check the generated migration file in `alembic/versions/` and review the changes:

- Ensure the upgrade and downgrade functions are correct
- Verify that data migration steps are included if needed
- Test the migration on a copy of your data

### 3. Apply the Migration

```bash
python migrate.py upgrade
```

### 4. Deploy to Production

In production environments, run migrations as part of your deployment process:

```bash
# In production deployment script
python migrate.py upgrade
```

## Docker Integration

For Docker deployments, you can run migrations in the container startup scripts. Both `web_app/start.sh` and `sync_app/start.sh` can include migration commands.

## CI/CD Integration

The GitHub Actions workflow automatically:

1. Sets up a test database
2. Runs `python migrate.py upgrade` to apply all migrations
3. Runs the test suite against the migrated database

## Troubleshooting

### Connection Issues

If you get database connection errors:

```bash
python migrate.py test-connection
```

### Migration Conflicts

If you have migration conflicts (multiple head revisions), merge them:

```bash
alembic merge heads -m "Merge migrations"
```

### Reset to Baseline

If you need to reset migrations (⚠️ **destructive operation**):

```bash
# Mark database as being at baseline
alembic stamp head

# Or start fresh (will lose migration history)
rm alembic/versions/*.py
alembic revision --autogenerate -m "Recreate schema"
```

## Best Practices

1. **Always review** auto-generated migrations before applying them
2. **Test migrations** on a copy of production data
3. **Include data migrations** when changing column types or constraints
4. **Use descriptive messages** for migration descriptions
5. **Backup your database** before running migrations in production
6. **Keep migrations small** and focused on specific changes

## Model Synchronization

Both `web_app/models/` and `sync_app/models/` should be kept in sync since they represent the same database schema. When updating models:

1. Update the model in one location
2. Copy/sync the changes to the other location
3. Generate a single migration that captures all changes
