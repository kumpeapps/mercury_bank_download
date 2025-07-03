from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Table, text
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

# Association table for granular user access to specific accounts within mercury accounts
# When this table has entries for a user, it restricts access to only those specific accounts
# If no entries exist for a user, they have access to all accounts in their mercury accounts (default behavior)
# Note: user_id does not have a foreign key constraint because users table might be a view
user_account_access = Table(
    "user_account_access",
    Base.metadata,
    Column("user_id", Integer, primary_key=True),
    Column("account_id", String(255), ForeignKey("accounts.id"), primary_key=True),
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
    """Initialize all database tables"""
    from .mercury_account import MercuryAccount
    from .account import Account
    from .transaction import Transaction
    from .user import User
    from .system_setting import SystemSetting
    from .user_settings import UserSettings
    from .role import Role, user_role_association

    engine, _ = create_engine_and_session()

    # Create tables in the correct order to satisfy foreign key constraints
    # 1. First create tables without foreign key dependencies
    User.__table__.create(bind=engine, checkfirst=True)
    MercuryAccount.__table__.create(bind=engine, checkfirst=True)
    SystemSetting.__table__.create(bind=engine, checkfirst=True)
    Role.__table__.create(bind=engine, checkfirst=True)

    # 2. Then create tables that depend on User
    UserSettings.__table__.create(bind=engine, checkfirst=True)

    # 3. Then create the association tables
    user_mercury_account_association.create(bind=engine, checkfirst=True)
    user_role_association.create(bind=engine, checkfirst=True)
    user_account_access.create(bind=engine, checkfirst=True)

    # 4. Finally create tables that depend on MercuryAccount
    Account.__table__.create(bind=engine, checkfirst=True)
    Transaction.__table__.create(bind=engine, checkfirst=True)

    return engine


def init_sync_db():
    """Initialize all database tables needed for syncing and user management"""
    from .mercury_account import MercuryAccount
    from .account import Account
    from .transaction import Transaction
    from .user import User
    from .system_setting import SystemSetting
    from .user_settings import UserSettings
    from .role import Role, user_role_association

    engine, _ = create_engine_and_session()

    print("Creating database tables...")
    
    # Create core tables first (in correct order for foreign keys)
    # Ensure they use InnoDB engine and proper charset
    try:
        User.__table__.create(bind=engine, checkfirst=True)
        print("Users table created successfully")
    except Exception as e:
        print(f"Users table creation failed, trying manual creation: {e}")
        with engine.connect() as connection:
            # Check if users table exists and what type it is
            result = connection.execute(text("""
                SELECT TABLE_TYPE 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = 'users'
            """))
            table_info = result.fetchone()
            
            if table_info:
                table_type = table_info[0]
                if table_type == 'VIEW':
                    print("Users table exists as a VIEW (managed by third-party system) - skipping creation")
                elif table_type == 'BASE TABLE':
                    print("Users table already exists as BASE TABLE")
                else:
                    print(f"Users table exists as {table_type}")
            else:
                # Table doesn't exist, create it
                connection.execute(text("""
                    CREATE TABLE users (
                        id INTEGER NOT NULL AUTO_INCREMENT,
                        username VARCHAR(100) NOT NULL,
                        email VARCHAR(255) NOT NULL,
                        password_hash VARCHAR(255) NOT NULL,
                        first_name VARCHAR(100),
                        last_name VARCHAR(100),
                        is_active BOOLEAN DEFAULT TRUE,
                        last_login DATETIME,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        PRIMARY KEY (id),
                        UNIQUE KEY unique_username (username),
                        UNIQUE KEY unique_email (email)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """))
                connection.commit()
                print("Users table created manually")
    
    try:
        MercuryAccount.__table__.create(bind=engine, checkfirst=True)
        print("MercuryAccount table created successfully")
    except Exception as e:
        print(f"MercuryAccount table creation failed, trying manual creation: {e}")
        with engine.connect() as connection:
            result = connection.execute(text("""
                SELECT COUNT(*) 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = 'mercury_accounts'
            """))
            if result.fetchone()[0] == 0:
                connection.execute(text("""
                    CREATE TABLE mercury_accounts (
                        id INTEGER NOT NULL AUTO_INCREMENT,
                        name VARCHAR(255) NOT NULL,
                        api_key VARCHAR(500) NOT NULL,
                        sandbox_mode BOOLEAN DEFAULT FALSE,
                        description TEXT,
                        is_active BOOLEAN DEFAULT TRUE,
                        sync_enabled BOOLEAN DEFAULT TRUE,
                        last_sync_at DATETIME,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        PRIMARY KEY (id)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """))
                connection.commit()
                print("MercuryAccount table created manually")
    
    SystemSetting.__table__.create(bind=engine, checkfirst=True)
    
    # Create UserSettings table manually to handle foreign key constraint issues
    try:
        UserSettings.__table__.create(bind=engine, checkfirst=True)
        print("UserSettings table created successfully with foreign keys")
    except Exception as e:
        print(f"UserSettings table creation with foreign keys failed: {e}")
        print("Creating UserSettings table without foreign keys and adding them separately...")
        
        # Create table structure without foreign keys first
        with engine.connect() as connection:
            # Check if table exists
            result = connection.execute(text("""
                SELECT COUNT(*) 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = 'user_settings'
            """))
            
            if result.fetchone()[0] == 0:
                # Create table without foreign key constraints
                connection.execute(text("""
                    CREATE TABLE user_settings (
                        id INTEGER NOT NULL AUTO_INCREMENT,
                        user_id INTEGER NOT NULL,
                        primary_mercury_account_id INTEGER,
                        dashboard_preferences JSON,
                        report_preferences JSON,
                        transaction_preferences JSON,
                        is_admin BOOLEAN DEFAULT FALSE NOT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        PRIMARY KEY (id),
                        UNIQUE KEY unique_user_id (user_id)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """))
                print("UserSettings table structure created")
                
                # Try to add foreign key constraints
                try:
                    connection.execute(text("""
                        ALTER TABLE user_settings 
                        ADD CONSTRAINT fk_user_settings_user_id 
                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                    """))
                    print("Added foreign key constraint for user_id")
                except Exception as fk_error:
                    print(f"Could not add user_id foreign key constraint: {fk_error}")
                
                try:
                    connection.execute(text("""
                        ALTER TABLE user_settings 
                        ADD CONSTRAINT fk_user_settings_mercury_account_id 
                        FOREIGN KEY (primary_mercury_account_id) REFERENCES mercury_accounts(id) ON DELETE SET NULL
                    """))
                    print("Added foreign key constraint for primary_mercury_account_id")
                except Exception as fk_error:
                    print(f"Could not add mercury_account_id foreign key constraint: {fk_error}")
                
                connection.commit()
                print("UserSettings table setup completed")
            else:
                print("UserSettings table already exists")
    
    # Handle association table creation
    association_table_created = False
    try:
        user_mercury_account_association.create(bind=engine, checkfirst=True)
        print("Association table created with foreign keys!")
        association_table_created = True
    except Exception as e:
        print(f"Association table creation with foreign keys failed: {e}")
        
    # If association table creation failed, create it manually and add constraints
    if not association_table_created:
        try:
            with engine.connect() as connection:
                # Check if table exists
                result = connection.execute(text("""
                    SELECT COUNT(*) 
                    FROM INFORMATION_SCHEMA.TABLES 
                    WHERE TABLE_SCHEMA = DATABASE() 
                    AND TABLE_NAME = 'user_mercury_accounts'
                """))
                
                if result.fetchone()[0] == 0:
                    # Create table structure first
                    connection.execute(text("""
                        CREATE TABLE user_mercury_accounts (
                            user_id INTEGER NOT NULL,
                            mercury_account_id INTEGER NOT NULL,
                            PRIMARY KEY (user_id, mercury_account_id)
                        )
                    """))
                    print("Association table structure created")
                
                # Try to add foreign key constraints
                try:
                    connection.execute(text("""
                        ALTER TABLE user_mercury_accounts 
                        ADD CONSTRAINT fk_user_mercury_user_id 
                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                    """))
                    print("Added foreign key constraint for user_id")
                except Exception:
                    print("Could not add user_id foreign key constraint (may already exist)")
                
                try:
                    connection.execute(text("""
                        ALTER TABLE user_mercury_accounts 
                        ADD CONSTRAINT fk_user_mercury_account_id 
                        FOREIGN KEY (mercury_account_id) REFERENCES mercury_accounts(id) ON DELETE CASCADE
                    """))
                    print("Added foreign key constraint for mercury_account_id")
                except Exception:
                    print("Could not add mercury_account_id foreign key constraint (may already exist)")
                
                connection.commit()
                print("Association table setup completed")
                
        except Exception as manual_error:
            print(f"Manual association table setup failed: {manual_error}")
            print("Continuing without foreign key constraints - relationships may not work properly")
    
    # Create remaining tables
    Account.__table__.create(bind=engine, checkfirst=True)
    Transaction.__table__.create(bind=engine, checkfirst=True)
    
    print("All tables created successfully!")
    return engine
