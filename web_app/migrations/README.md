# Web App Database Migrations

This directory contains SQLAlchemy-based database migration files for the web application.

## Structure

Migration files should follow the naming convention:

```text
NNN_description.py
```

Where:

- `NNN` is a zero-padded sequence number (001, 002, etc.)
- `description` is a brief description of the migration

## Migration Format

Each migration file should be a Python module with the following structure:

```python
"""
Migration description here
"""

from sqlalchemy import text


def upgrade(engine):
    """Apply the migration"""
    # Your SQLAlchemy operations here
    pass


def downgrade(engine):
    """Rollback the migration (optional)"""
    # Your SQLAlchemy rollback operations here
    pass
```

## Notes

- Only Python/SQLAlchemy migrations are supported
- Each migration must have an `upgrade(engine)` function
- The `downgrade(engine)` function is optional but recommended
- Use SQLAlchemy operations whenever possible for database portability
