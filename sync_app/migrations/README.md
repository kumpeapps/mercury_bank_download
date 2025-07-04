# Database Migrations

This directory contains database migration files for the Mercury Bank Integration Platform.

## Migration System Overview

The migration system is designed to handle database schema changes across different releases while maintaining data integrity and allowing for rollbacks when necessary.

## First Production Release (v1.0)

For the first production release, we use SQLAlchemy's `create_all()` approach to establish the complete initial schema. This is handled by the `initial_setup.py` script which creates:

- All database tables using SQLAlchemy models
- Initial system roles (user, admin, super-admin, reports)
- Initial system settings
- Proper foreign key relationships and constraints

## Future Releases

Starting from v1.1, all database changes should be implemented as migration files in this directory following the pattern:

```
001_descriptive_migration_name.py
002_another_migration_name.py
...
```

### Migration File Structure

Each migration file should follow this template:

```python
"""
Migration: [Description of what this migration does]
Created: [Date]
"""

def upgrade(engine):
    """
    Apply the migration
    """
    # Implementation here
    pass

def downgrade(engine):
    """
    Rollback the migration
    """
    # Implementation here
    pass
```

### Migration Guidelines

1. **Always include both upgrade() and downgrade() functions**
2. **Use SQLAlchemy operations when possible** rather than raw SQL
3. **Test migrations thoroughly** in development environment
4. **Make migrations idempotent** - they should be safe to run multiple times
5. **Include proper error handling** and logging
6. **Document breaking changes** in migration comments

### Running Migrations

Migrations are automatically executed during container startup by the migration manager. The system:

1. Checks for pending migrations
2. Executes them in order
3. Records successful migrations in the `migrations` table
4. Provides rollback capabilities if needed

### Migration Manager

The migration manager (`migration_manager.py`) handles:

- Tracking which migrations have been applied
- Executing pending migrations in the correct order
- Logging migration results
- Providing rollback functionality
- Ensuring database consistency

## Development Workflow

1. **For the first release**: Use `initial_setup.py` to create the base schema
2. **For future releases**: Create new migration files in this directory
3. **Test locally**: Use `./dev.sh reset-db` to test with fresh database
4. **Validate in staging**: Ensure migrations work with existing data
5. **Deploy to production**: Migrations run automatically during deployment

## Database Schema Evolution

The schema will evolve through migrations, with each migration building upon the previous state. The migration system ensures:

- **Version control**: Each database change is tracked and versioned
- **Consistency**: All environments can be brought to the same schema state
- **Rollback capability**: Changes can be undone if issues arise
- **Data preservation**: Migrations handle data transformations safely

## Troubleshooting

If you encounter migration issues:

1. Check the application logs for detailed error messages
2. Verify the migration file syntax and logic
3. Test the migration in a development environment
4. Use the rollback functionality if needed
5. Consult the migration history in the `migrations` table

For production issues, refer to the deployment documentation for recovery procedures.
