"""
Migration for adding role-based access control.
This migration creates the roles table and user_roles association table.
"""

from sqlalchemy import Column, String, DateTime, Boolean, text, Integer, Table, ForeignKey, MetaData, inspect

def upgrade(engine=None):
    """Create the necessary tables for role-based access control"""
    from sqlalchemy import create_engine
    import os
    from sqlalchemy.schema import CreateTable
    
    # Create engine from env variable if not provided
    if engine is None:
        engine = create_engine(
            os.getenv("DATABASE_URL", "mysql+pymysql://user:password@localhost/mercury_bank"),
            connect_args={"charset": "utf8mb4"},
        )
    
    # Get inspector to check if tables exist
    inspector = inspect(engine)
    
    # Only create the roles table if it doesn't exist
    if not inspector.has_table("roles"):
        # Create MetaData instance
        metadata = MetaData()
        
        # Define roles table
        roles_table = Table(
            "roles",
            metadata,
            Column("id", Integer, primary_key=True, autoincrement=True, nullable=False),
            Column("name", String(50), unique=True, nullable=False),
            Column("description", String(255), nullable=True),
            Column("is_system_role", Boolean, default=False, nullable=False),
            Column("created_at", DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP")),
            Column("updated_at", DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"), 
                  onupdate=text("CURRENT_TIMESTAMP")),
        )
        
        # Create roles table
        with engine.connect() as conn:
            conn.execute(CreateTable(roles_table))
            conn.commit()
            print("Created roles table")
            
            # Insert default roles
            conn.execute(
                text("""
                INSERT INTO roles (name, description, is_system_role) VALUES 
                ('super-admin', 'Full access to all system features including user management and system settings', TRUE),
                ('admin', 'Can manage Mercury accounts and account settings', TRUE),
                ('user', 'Basic user with access to assigned accounts', TRUE),
                ('reports', 'Access to reports functionality', TRUE),
                ('transactions', 'Access to transactions functionality', TRUE),
                ('locked', 'Restricted access, cannot log in', TRUE)
                """)
            )
            conn.commit()
            print("Inserted default roles")
    
    # Only create the user_roles table if it doesn't exist
    if not inspector.has_table("user_roles"):
        # First, let's check the structure of the users table to ensure compatibility
        with engine.connect() as conn:
            # Get the users table structure
            users_columns = inspector.get_columns("users")
            users_id_type = None
            for col in users_columns:
                if col["name"] == "id":
                    users_id_type = col["type"]
                    break
            
            # Get the roles table structure
            roles_columns = inspector.get_columns("roles")
            roles_id_type = None
            for col in roles_columns:
                if col["name"] == "id":
                    roles_id_type = col["type"]
                    break
            
            print(f"Users.id type: {users_id_type}")
            print(f"Roles.id type: {roles_id_type}")
            
            # Create user_roles table with proper column types
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS user_roles (
                    user_id INT NOT NULL,
                    role_id INT NOT NULL,
                    PRIMARY KEY (user_id, role_id),
                    INDEX idx_user_roles_user_id (user_id),
                    INDEX idx_user_roles_role_id (role_id)
                )
            """))
            conn.commit()
            print("Created user_roles table without foreign keys first")
            
            # Now add the foreign key constraints
            try:
                conn.execute(text("""
                    ALTER TABLE user_roles 
                    ADD CONSTRAINT fk_user_roles_user_id 
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                """))
                conn.commit()
                print("Added foreign key constraint for user_id")
            except Exception as e:
                print(f"Warning: Could not add user_id foreign key: {e}")
            
            try:
                conn.execute(text("""
                    ALTER TABLE user_roles 
                    ADD CONSTRAINT fk_user_roles_role_id 
                    FOREIGN KEY (role_id) REFERENCES roles (id) ON DELETE CASCADE
                """))
                conn.commit()
                print("Added foreign key constraint for role_id")
            except Exception as e:
                print(f"Warning: Could not add role_id foreign key: {e}")
                
            print("Created user_roles table")
    
    # Grant existing admin users the admin role
    with engine.connect() as conn:
        # Check if any users exist at all (for first user case)
        user_count = conn.execute(text("SELECT COUNT(*) FROM users")).scalar()
        
        if user_count > 0:
            # Get admin role ID
            admin_role_id = conn.execute(text("SELECT id FROM roles WHERE name = 'admin'")).scalar()
            super_admin_role_id = conn.execute(text("SELECT id FROM roles WHERE name = 'super-admin'")).scalar()
            
            # First user should be super-admin
            first_user_id = conn.execute(text("SELECT id FROM users ORDER BY id LIMIT 1")).scalar()
            
            # Only add if not already assigned
            if not conn.execute(
                text(f"SELECT 1 FROM user_roles WHERE user_id = {first_user_id} AND role_id = {super_admin_role_id}")
            ).scalar():
                conn.execute(
                    text(f"INSERT INTO user_roles (user_id, role_id) VALUES ({first_user_id}, {super_admin_role_id})")
                )
                print(f"Assigned super-admin role to first user (ID: {first_user_id})")
            
            # Assign admin role to all users with admin settings
            admin_users = conn.execute(
                text("""
                SELECT u.id 
                FROM users u 
                JOIN user_settings us ON u.id = us.user_id 
                WHERE us.is_admin = TRUE
                """)
            ).fetchall()
            
            for user in admin_users:
                user_id = user[0]
                # Skip the first user (already super-admin)
                if user_id == first_user_id:
                    continue
                    
                # Only add if not already assigned
                if not conn.execute(
                    text(f"SELECT 1 FROM user_roles WHERE user_id = {user_id} AND role_id = {admin_role_id}")
                ).scalar():
                    conn.execute(
                        text(f"INSERT INTO user_roles (user_id, role_id) VALUES ({user_id}, {admin_role_id})")
                    )
                    print(f"Assigned admin role to existing admin user (ID: {user_id})")
                    
            # Grant super-admin role to SUPER_ADMIN_USERNAME if set
            super_admin_username = os.getenv("SUPER_ADMIN_USERNAME")
            if super_admin_username:
                super_admin_user = conn.execute(
                    text(f"SELECT id FROM users WHERE username = '{super_admin_username}'")
                ).scalar()
                
                if super_admin_user:
                    # Only add if not already assigned
                    if not conn.execute(
                        text(f"SELECT 1 FROM user_roles WHERE user_id = {super_admin_user} AND role_id = {super_admin_role_id}")
                    ).scalar():
                        conn.execute(
                            text(f"INSERT INTO user_roles (user_id, role_id) VALUES ({super_admin_user}, {super_admin_role_id})")
                        )
                        print(f"Assigned super-admin role to SUPER_ADMIN_USERNAME user (ID: {super_admin_user})")
            
            # All other users get the 'user' role
            user_role_id = conn.execute(text("SELECT id FROM roles WHERE name = 'user'")).scalar()
            
            # Add transactions and reports role to all users (to maintain backward compatibility)
            transactions_role_id = conn.execute(text("SELECT id FROM roles WHERE name = 'transactions'")).scalar()
            reports_role_id = conn.execute(text("SELECT id FROM roles WHERE name = 'reports'")).scalar()
            
            all_users = conn.execute(text("SELECT id FROM users")).fetchall()
            for user in all_users:
                user_id = user[0]
                
                # Assign 'user' role if not already assigned
                if not conn.execute(
                    text(f"SELECT 1 FROM user_roles WHERE user_id = {user_id} AND role_id = {user_role_id}")
                ).scalar():
                    conn.execute(
                        text(f"INSERT INTO user_roles (user_id, role_id) VALUES ({user_id}, {user_role_id})")
                    )
                
                # Assign 'transactions' role if not already assigned
                if not conn.execute(
                    text(f"SELECT 1 FROM user_roles WHERE user_id = {user_id} AND role_id = {transactions_role_id}")
                ).scalar():
                    conn.execute(
                        text(f"INSERT INTO user_roles (user_id, role_id) VALUES ({user_id}, {transactions_role_id})")
                    )
                
                # Assign 'reports' role if not already assigned
                if not conn.execute(
                    text(f"SELECT 1 FROM user_roles WHERE user_id = {user_id} AND role_id = {reports_role_id}")
                ).scalar():
                    conn.execute(
                        text(f"INSERT INTO user_roles (user_id, role_id) VALUES ({user_id}, {reports_role_id})")
                    )
            
            print("Assigned basic roles to all users")
            
        conn.commit()

def downgrade(engine=None):
    """Remove the role-based access control tables"""
    from sqlalchemy import create_engine
    import os
    
    # Create engine from env variable if not provided
    if engine is None:
        engine = create_engine(
            os.getenv("DATABASE_URL", "mysql+pymysql://user:password@localhost/mercury_bank"),
            connect_args={"charset": "utf8mb4"},
        )
    
    # Get inspector to check if tables exist
    inspector = inspect(engine)
    
    # Drop the user_roles table if it exists
    if inspector.has_table("user_roles"):
        with engine.connect() as conn:
            conn.execute(text("DROP TABLE user_roles"))
            conn.commit()
            print("Dropped user_roles table")
    
    # Drop the roles table if it exists
    if inspector.has_table("roles"):
        with engine.connect() as conn:
            conn.execute(text("DROP TABLE roles"))
            conn.commit()
            print("Dropped roles table")
