from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

Base = declarative_base()

def get_database_url():
    """Get database URL from environment variables"""
    return os.getenv(
        'DATABASE_URL',
        'mysql+pymysql://user:password@localhost/mercury_bank'
    )

def create_engine_and_session():
    """Create database engine and session"""
    engine = create_engine(get_database_url())
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return engine, SessionLocal

def init_db():
    """Initialize database tables"""
    engine, _ = create_engine_and_session()
    Base.metadata.create_all(bind=engine)
    return engine
