from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, Column, Integer, ForeignKey, Table, text
from sqlalchemy.orm import sessionmaker
import os

Base = declarative_base()

# Association table for many-to-many relationship between users and mercury accounts
# Defined here to avoid circular import issues
user_mercury_account_association = Table(
    "user_mercury_accounts",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("mercury_account_id", Integer, ForeignKey("mercury_accounts.id"), primary_key=True),
)

# Association table for many-to-many relationship between users and roles
user_role_association = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("role_id", Integer, ForeignKey("roles.id"), primary_key=True),
)


def get_database_url():
    """Get database URL from environment variables"""
    return os.getenv(
        "DATABASE_URL", "mysql+pymysql://user:password@localhost/mercury_bank"
    )


def create_engine_and_session():
    """Create database engine and session"""
    engine = create_engine(
        get_database_url(),
        connect_args={
            "charset": "utf8mb4"
        },
        echo=False
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return engine, SessionLocal


def init_db():
    """Initialize all database tables using SQLAlchemy create_all"""
    engine, _ = create_engine_and_session()
    
    # Create all tables defined in the models
    Base.metadata.create_all(engine)
    
    return engine


def init_sync_db():
    """Initialize all database tables needed for syncing and user management"""
    engine, _ = create_engine_and_session()

    print("Creating database tables...")
    
    try:
        # Create all tables defined in the models
        # The checkfirst=True parameter ensures tables are only created if they don't exist
        Base.metadata.create_all(engine, checkfirst=True)
        print("Database tables created successfully")
    except Exception as e:
        print(f"Database table creation failed: {e}")
        raise e
    
    return engine
