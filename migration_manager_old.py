"""
Migration system for Mercury Bank application.

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
    """Manages database migrations for the Mercury Bank application."""

    def __init__(self, database_url: str):
        """
        Initialize the migration manager.
        
        Args:
            database_url (str): Database connection URL
        """
        self.database_url = database_url
        self.migrations_dir = os.path.join(os.path.dirname(__file__), "migrations")
        self._parse_database_url(database_url)

    def _parse_database_url(self, database_url: str):
        """Parse database URL into connection parameters."""
        # Expected format: mysql+pymysql://user:password@host:port/database
        if database_url.startswith("mysql+pymysql://"):
            url = database_url.replace("mysql+pymysql://", "")
        elif database_url.startswith("mysql://"):
            url = database_url.replace("mysql://", "")
        else:
            raise ValueError("Unsupported database URL format")

        try:
            # Split user:password@host:port/database
            auth_host, database = url.split("/", 1)
            auth, host_port = auth_host.split("@", 1)
            
            if ":" in auth:
                self.user, self.password = auth.split(":", 1)
            else:
                self.user = auth
                self.password = ""

            if ":" in host_port:
                self.host, port_str = host_port.split(":", 1)
                self.port = int(port_str)
            else:
                self.host = host_port
                self.port = 3306

            self.database = database
        except ValueError as e:
            raise ValueError(f"Invalid database URL format: {e}")

    def get_connection(self):
        """Get a database connection with compatibility settings."""
        try:
            connection = mysql.connector.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                autocommit=False,
                charset='utf8mb4',
                collation='utf8mb4_general_ci',  # Use compatible collation
                use_unicode=True,
                sql_mode='',  # Disable strict mode for compatibility
                connection_timeout=10,
                auth_plugin='mysql_native_password'  # Use compatible auth plugin
            )
            return connection
        except Error as e:
            logger.error(f"Error connecting to database: {e}")
            raise

    def ensure_migrations_table(self):
        """Ensure the migrations tracking table exists."""
        connection = None
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            
            # Create migrations table if it doesn't exist
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS migrations (
                id INT AUTO_INCREMENT PRIMARY KEY,
                filename VARCHAR(255) NOT NULL UNIQUE,
                checksum VARCHAR(64) NOT NULL,
                executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_filename (filename)
            )
            """
            cursor.execute(create_table_sql)
            connection.commit()
            logger.info("Migrations table ensured")
            
        except Error as e:
            logger.error(f"Error ensuring migrations table: {e}")
            if connection:
                connection.rollback()
            raise
        finally:
            if connection and connection.is_connected():
                cursor.close()
                connection.close()

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
        connection = None
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            
            cursor.execute("SELECT filename, checksum FROM migrations")
            results = cursor.fetchall()
            
            return {filename: checksum for filename, checksum in results}
            
        except Error as e:
            logger.error(f"Error getting executed migrations: {e}")
            return {}
        finally:
            if connection and connection.is_connected():
                cursor.close()
                connection.close()

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
            logger.error(f"Migration file not found: {filepath}")
            return False

        connection = None
        try:
            # Read migration content
            with open(filepath, 'r', encoding='utf-8') as f:
                migration_content = f.read()

            # Calculate checksum
            checksum = self.calculate_file_checksum(filepath)

            # Execute migration
            connection = self.get_connection()
            cursor = connection.cursor()

            # Split statements by semicolon and execute each one
            statements = [stmt.strip() for stmt in migration_content.split(';') if stmt.strip()]
            
            for statement in statements:
                if statement:
                    logger.info(f"Executing SQL: {statement[:100]}...")
                    cursor.execute(statement)

            # Record migration as executed
            cursor.execute(
                "INSERT INTO migrations (filename, checksum) VALUES (%s, %s)",
                (filename, checksum)
            )
            
            connection.commit()
            logger.info(f"Successfully executed migration: {filename}")
            return True

        except Error as e:
            logger.error(f"Error executing migration {filename}: {e}")
            if connection:
                connection.rollback()
            return False
        except Exception as e:
            logger.error(f"Unexpected error executing migration {filename}: {e}")
            if connection:
                connection.rollback()
            return False
        finally:
            if connection and connection.is_connected():
                cursor.close()
                connection.close()

    def validate_migration_checksum(self, filename: str, stored_checksum: str) -> bool:
        """Validate that a migration file hasn't been modified."""
        filepath = os.path.join(self.migrations_dir, filename)
        
        if not os.path.exists(filepath):
            logger.warning(f"Migration file missing: {filename}")
            return False

        current_checksum = self.calculate_file_checksum(filepath)
        if current_checksum != stored_checksum:
            logger.warning(f"Migration file modified: {filename}")
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
                    logger.error(f"Migration validation failed for: {filename}")
                    return False

            # Execute pending migrations
            pending_migrations = [f for f in migration_files if f not in executed_migrations]
            
            if not pending_migrations:
                logger.info("No pending migrations")
                return True

            logger.info(f"Found {len(pending_migrations)} pending migrations")
            
            for filename in pending_migrations:
                logger.info(f"Executing migration: {filename}")
                if not self.execute_migration(filename):
                    logger.error(f"Migration failed: {filename}")
                    return False

            logger.info("All migrations completed successfully")
            return True

        except Exception as e:
            logger.error(f"Migration process failed: {e}")
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
