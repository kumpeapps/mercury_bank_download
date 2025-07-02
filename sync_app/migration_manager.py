"""
SQLAlchemy-based migration system for Mercury Bank application.

This module provides functionality to automatically run database migrations
when the application starts, ensuring the database schema is always up to date.
Uses SQLAlchemy for database-agnostic operations.
"""

import os
import logging
from typing import List, Dict, Optional
import hashlib
from datetime import datetime
from sqlalchemy import create_engine, text, Column, Integer, String, DateTime, MetaData, Table
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.engine import Engine

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MigrationManager:
    """Manages database migrations for the Mercury Bank application using SQLAlchemy."""

    def __init__(self, database_url: str):
        """
        Initialize the migration manager.
        
        Args:
            database_url (str): Database connection URL
        """
        self.database_url = database_url
        self.migrations_dir = os.path.join(os.path.dirname(__file__), "migrations")
        self.engine = create_engine(database_url)
        self.Session = sessionmaker(bind=self.engine)
        self.metadata = MetaData()
        self._define_migrations_table()

    def _define_migrations_table(self):
        """Define the migrations table structure."""
        self.migrations_table = Table(
            'migrations',
            self.metadata,
            Column('id', Integer, primary_key=True, autoincrement=True),
            Column('filename', String(255), nullable=False, unique=True),
            Column('checksum', String(64), nullable=False),
            Column('executed_at', DateTime, nullable=False, default=datetime.utcnow)
        )

    def test_connection(self) -> bool:
        """Test database connection."""
        try:
            with self.engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            return True
        except SQLAlchemyError as e:
            logger.error("Database connection test failed: %s", e)
            return False

    def ensure_migrations_table(self):
        """Ensure the migrations tracking table exists."""
        try:
            # Create migrations table if it doesn't exist
            self.migrations_table.create(self.engine, checkfirst=True)
            logger.info("Migrations table ensured")
            
        except SQLAlchemyError as e:
            logger.error("Error ensuring migrations table: %s", e)
            raise

    def get_migration_files(self) -> List[str]:
        """Get list of migration files sorted by filename."""
        if not os.path.exists(self.migrations_dir):
            logger.info("Migrations directory does not exist")
            return []

        migration_files = []
        for filename in os.listdir(self.migrations_dir):
            if filename.endswith('.sql'):
                migration_files.append(filename)
        
        return sorted(migration_files)

    def get_executed_migrations(self) -> Dict[str, str]:
        """Get list of already executed migrations with their checksums."""
        session = self.Session()
        try:
            results = session.execute(
                text("SELECT filename, checksum FROM migrations")
            ).fetchall()
            
            return {row.filename: row.checksum for row in results}
            
        except SQLAlchemyError as e:
            logger.error("Error getting executed migrations: %s", e)
            return {}
        finally:
            session.close()

    def calculate_file_checksum(self, filepath: str) -> str:
        """Calculate MD5 checksum of a file."""
        hash_md5 = hashlib.md5()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def execute_migration(self, filename: str) -> bool:
        """
        Execute a single migration file.
        
        Args:
            filename (str): Name of the migration file
            
        Returns:
            bool: True if successful, False otherwise
        """
        filepath = os.path.join(self.migrations_dir, filename)
        
        if not os.path.exists(filepath):
            logger.error("Migration file not found: %s", filepath)
            return False

        session = self.Session()
        try:
            # Read migration content
            with open(filepath, 'r', encoding='utf-8') as f:
                migration_content = f.read()

            # Calculate checksum
            checksum = self.calculate_file_checksum(filepath)

            # Begin transaction
            session.begin()

            # Remove comments first
            lines = [line for line in migration_content.split('\n') 
                    if line.strip() and not line.strip().startswith('--')]
            content_without_comments = '\n'.join(lines)
            
            # Split by semicolon to get individual statements
            statements = [stmt.strip() for stmt in content_without_comments.split(';') if stmt.strip()]
            
            for statement in statements:
                if statement:
                    logger.info("Executing SQL statement...")
                    session.execute(text(statement))

            # Record migration as executed
            session.execute(
                text("INSERT INTO migrations (filename, checksum, executed_at) VALUES (:filename, :checksum, :executed_at)"),
                {
                    "filename": filename,
                    "checksum": checksum,
                    "executed_at": datetime.utcnow()
                }
            )
            
            session.commit()
            logger.info("Successfully executed migration: %s", filename)
            return True

        except SQLAlchemyError as e:
            logger.error("Error executing migration %s: %s", filename, e)
            session.rollback()
            return False
        except Exception as e:
            logger.error("Unexpected error executing migration %s: %s", filename, e)
            session.rollback()
            return False
        finally:
            session.close()

    def validate_migration_checksum(self, filename: str, stored_checksum: str) -> bool:
        """Validate that a migration file hasn't been modified."""
        filepath = os.path.join(self.migrations_dir, filename)
        
        if not os.path.exists(filepath):
            logger.warning("Migration file missing: %s", filename)
            return False

        current_checksum = self.calculate_file_checksum(filepath)
        if current_checksum != stored_checksum:
            logger.warning("Migration file modified: %s", filename)
            return False

        return True

    def run_migrations(self) -> bool:
        """
        Run all pending migrations.
        
        Returns:
            bool: True if all migrations successful, False otherwise
        """
        try:
            logger.info("Starting migration process...")
            
            # Test database connection first
            if not self.test_connection():
                logger.error("Database connection failed")
                return False
            
            # Ensure migrations table exists
            self.ensure_migrations_table()
            
            # Get migration files and executed migrations
            migration_files = self.get_migration_files()
            executed_migrations = self.get_executed_migrations()
            
            if not migration_files:
                logger.info("No migration files found")
                return True

            # Validate already executed migrations
            for filename, checksum in executed_migrations.items():
                if not self.validate_migration_checksum(filename, checksum):
                    logger.error("Migration validation failed for: %s", filename)
                    return False

            # Execute pending migrations
            pending_migrations = [f for f in migration_files if f not in executed_migrations]
            
            if not pending_migrations:
                logger.info("No pending migrations")
                return True

            logger.info("Found %d pending migrations", len(pending_migrations))
            
            for filename in pending_migrations:
                logger.info("Executing migration: %s", filename)
                if not self.execute_migration(filename):
                    logger.error("Migration failed: %s", filename)
                    return False

            logger.info("All migrations completed successfully")
            return True

        except Exception as e:
            logger.error("Migration process failed: %s", e)
            return False


def run_migrations_from_env():
    """Run migrations using environment variables for database connection."""
    database_url = os.environ.get(
        "DATABASE_URL", 
        "mysql+pymysql://user:password@db:3306/mercury_bank"
    )
    
    migration_manager = MigrationManager(database_url)
    success = migration_manager.run_migrations()
    
    if not success:
        logger.error("Migration process failed")
        exit(1)
    else:
        logger.info("Migration process completed successfully")


if __name__ == "__main__":
    run_migrations_from_env()
