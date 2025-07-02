#!/usr/bin/env python3
"""
Create the missing user_mercury_accounts table

This script creates the user_mercury_accounts association table that is required
for the many-to-many relationship between users and mercury_accounts.
"""

import os
import sys
import pymysql
from urllib.parse import urlparse

def get_db_connection():
    """Get database connection from DATABASE_URL environment variable or docker-compose.yml"""
    # Try to get from environment first
    database_url = os.getenv('DATABASE_URL')
    
    # If not in environment, use the one from docker-compose.yml
    if not database_url:
        database_url = "mysql+pymysql://Bot_mercury:LetmeN2it@172.16.21.10:3306/Bot_mercury"
    
    # Parse the URL
    if database_url.startswith('mysql+pymysql://'):
        database_url = database_url.replace('mysql+pymysql://', 'mysql://')
    
    parsed = urlparse(database_url)
    
    return pymysql.connect(
        host=parsed.hostname,
        port=parsed.port or 3306,
        user=parsed.username,
        password=parsed.password,
        database=parsed.path.lstrip('/'),
        charset='utf8mb4'
    )

def create_user_mercury_accounts_table():
    """Create the user_mercury_accounts table"""
    connection = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        print("Connected to database successfully!")
        
        # Create the table
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS user_mercury_accounts (
            user_id INT NOT NULL,
            mercury_account_id INT NOT NULL,
            PRIMARY KEY (user_id, mercury_account_id),
            INDEX idx_user_id (user_id),
            INDEX idx_mercury_account_id (mercury_account_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
        
        cursor.execute(create_table_sql)
        print("✅ user_mercury_accounts table created successfully!")
        
        # Check if users table exists for foreign key
        cursor.execute("""
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_SCHEMA = DATABASE() 
            AND TABLE_NAME = 'users'
        """)
        users_exists = cursor.fetchone()[0] > 0
        
        # Check if mercury_accounts table exists for foreign key
        cursor.execute("""
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_SCHEMA = DATABASE() 
            AND TABLE_NAME = 'mercury_accounts'
        """)
        mercury_accounts_exists = cursor.fetchone()[0] > 0
        
        # Add foreign key constraints if tables exist
        if users_exists:
            try:
                cursor.execute("""
                    ALTER TABLE user_mercury_accounts 
                    ADD CONSTRAINT fk_user_mercury_accounts_user_id 
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                """)
                print("✅ Foreign key constraint added for user_id")
            except pymysql.err.IntegrityError as e:
                if "Duplicate key name" in str(e):
                    print("ℹ️  Foreign key constraint for user_id already exists")
                else:
                    print(f"⚠️  Could not add foreign key constraint for user_id: {e}")
        else:
            print("ℹ️  Users table does not exist - skipping foreign key constraint")
            
        if mercury_accounts_exists:
            try:
                cursor.execute("""
                    ALTER TABLE user_mercury_accounts 
                    ADD CONSTRAINT fk_user_mercury_accounts_mercury_account_id 
                    FOREIGN KEY (mercury_account_id) REFERENCES mercury_accounts(id) ON DELETE CASCADE
                """)
                print("✅ Foreign key constraint added for mercury_account_id")
            except pymysql.err.IntegrityError as e:
                if "Duplicate key name" in str(e):
                    print("ℹ️  Foreign key constraint for mercury_account_id already exists")
                else:
                    print(f"⚠️  Could not add foreign key constraint for mercury_account_id: {e}")
        else:
            print("ℹ️  Mercury_accounts table does not exist - skipping foreign key constraint")
        
        # Show table structure
        cursor.execute("DESCRIBE user_mercury_accounts")
        columns = cursor.fetchall()
        
        print("\n📋 Table structure:")
        print("Column\t\tType\t\tNull\tKey\tDefault\tExtra")
        print("-" * 60)
        for column in columns:
            print(f"{column[0]}\t\t{column[1]}\t{column[2]}\t{column[3]}\t{column[4]}\t{column[5]}")
        
        connection.commit()
        print("\n🎉 All operations completed successfully!")
        
    except pymysql.err.OperationalError as e:
        print(f"❌ Database connection error: {e}")
        print("Please check your database credentials and ensure the database server is running.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    finally:
        if connection:
            connection.close()

if __name__ == "__main__":
    print("🔧 Creating user_mercury_accounts table...")
    create_user_mercury_accounts_table()
