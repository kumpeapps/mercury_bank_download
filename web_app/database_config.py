"""
Database configuration and optimization for Mercury Bank Web Application.
Includes connection pooling, caching, and query optimization.
"""

import os
import logging
import time
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class DatabaseConfig:
    """Optimized database configuration for high performance."""
    
    def __init__(self):
        self.database_url = os.environ.get(
            "DATABASE_URL", "mysql+pymysql://user:password@db:3306/mercury_bank"
        )
        
        # Performance-optimized engine configuration
        self.engine = create_engine(
            self.database_url,
            # Connection pooling for better performance
            poolclass=QueuePool,
            pool_size=20,          # Number of connections to keep persistently
            max_overflow=30,       # Additional connections that can be created on demand
            pool_pre_ping=True,    # Verify connections before use
            pool_recycle=3600,     # Recycle connections every hour
            
            # Connection optimization
            connect_args={
                "charset": "utf8mb4",
                "autocommit": True,
                "connect_timeout": 10,
                "read_timeout": 30,
                "write_timeout": 30,
            },
            
            # Query optimization
            echo=False,  # Set to True for SQL debugging
            isolation_level="READ_COMMITTED",
            
            # Performance tuning
            query_cache_size=1200,
        )
        
        # Scoped session for thread safety and better performance
        self.Session = scoped_session(sessionmaker(bind=self.engine))
        
        # Set up performance monitoring
        self._setup_performance_monitoring()
    
    def _setup_performance_monitoring(self):
        """Set up database performance monitoring."""
        
        @event.listens_for(self.engine, "before_cursor_execute")
        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            context._query_start_time = time.time()
        
        @event.listens_for(self.engine, "after_cursor_execute")
        def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            total = time.time() - context._query_start_time
            if total > 0.1:  # Log slow queries (>100ms)
                logger.warning(f"Slow query ({total:.3f}s): {statement[:100]}...")
    
    @contextmanager
    def get_session(self):
        """Context manager for database sessions with automatic cleanup."""
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def get_scoped_session(self):
        """Get a scoped session for the current thread."""
        return self.Session
    
    def close_session(self):
        """Remove the scoped session for the current thread."""
        self.Session.remove()

# Global database configuration instance
db_config = DatabaseConfig()

# Export commonly used objects
engine = db_config.engine
Session = db_config.Session
get_db_session = db_config.get_session
