# Mercury Bank Multi-Account Management

This document explains the new User and MercuryAccount models that enable multi-account management and user access control.

## Overview

The system now supports:
- **Multiple Mercury Bank account groups** with different API keys
- **User management** with login and access control
- **Flexible permissions** where users can access multiple account groups
- **Automatic synchronization** across all active account groups

## New Models

### User Model (`models/user.py`)

The User model manages user authentication and profiles:

```python
class User(Base):
    id = Column(String(255), primary_key=True)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"), onupdate=text("CURRENT_TIMESTAMP"))
    
    # Many-to-many relationship with MercuryAccount
    mercury_accounts = relationship("MercuryAccount", secondary=user_mercury_account_association, back_populates="users")
```

### MercuryAccount Model (`models/mercury_account.py`)

The MercuryAccount model stores Mercury Bank API credentials and configuration:

```python
class MercuryAccount(Base):
    id = Column(String(255), primary_key=True)
    name = Column(String(255), nullable=False)
    api_key = Column(String(500), nullable=False)
    sandbox_mode = Column(Boolean, default=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    sync_enabled = Column(Boolean, default=True)
    last_sync_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"), onupdate=text("CURRENT_TIMESTAMP"))
    
    # Many-to-many relationship with User
    users = relationship("User", secondary=user_mercury_account_association, back_populates="mercury_accounts")
    
    # One-to-many relationship with Account
    accounts = relationship("Account", back_populates="mercury_account")
```

### Updated Account Model

The Account model now includes a link to the Mercury account group:

```python
class Account(Base):
    # ... existing fields ...
    mercury_account_id = Column(String(255), ForeignKey("mercury_accounts.id"), nullable=True)
    
    # Relationship to mercury account group
    mercury_account = relationship("MercuryAccount", back_populates="accounts")
```

## Database Setup

### For New Installations

1. Run the setup script:
   ```bash
   python setup_db.py
   ```

2. Choose to create sample data when prompted

3. Update the sample data with real API keys and password hashes

### For Existing Installations

1. Run the migration script:
   ```bash
   mysql -u username -p database_name < migration.sql
   ```

2. Create Mercury account groups and users manually or using the setup script

## How Synchronization Works

The sync script now:

1. **Queries all active Mercury account groups** from the `mercury_accounts` table
2. **Loops through each group** and creates a Mercury API client with that group's API key
3. **Syncs accounts and transactions** for each group separately
4. **Associates accounts** with their respective Mercury account group
5. **Continues on errors** - if one group fails, others still sync

### Environment Variables

The sync script no longer requires `MERCURY_API_KEY` as an environment variable since API keys are stored in the database. Other environment variables remain the same:

- `SYNC_DAYS_BACK`: Number of days back to sync transactions (default: 30)
- `SYNC_INTERVAL_MINUTES`: Interval between sync runs (default: 60)
- `RUN_ONCE`: Run once and exit if 'true' (default: false)
- `DATABASE_URL`: Database connection string

## User Management Examples

### Creating a Mercury Account Group

```python
from models import MercuryAccount
import uuid

mercury_account = MercuryAccount(
    id=str(uuid.uuid4()),
    name="Company A Mercury Account",
    api_key="your_mercury_api_key_here",
    sandbox_mode=False,  # Set to True for testing
    description="Primary Mercury account for Company A",
    is_active=True,
    sync_enabled=True
)

db.add(mercury_account)
db.commit()
```

### Creating a User

```python
from models import User
import uuid
import bcrypt

# Hash password
password = "secure_password"
password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

user = User(
    id=str(uuid.uuid4()),
    username="john_doe",
    email="john@company.com",
    password_hash=password_hash,
    first_name="John",
    last_name="Doe",
    is_active=True
)
)

# Associate user with Mercury account groups
user.mercury_accounts.append(mercury_account)

db.add(user)
db.commit()
```

### Granting User Access to Multiple Account Groups

```python
# Get user and Mercury accounts
user = db.query(User).filter(User.username == "john_doe").first()
mercury_account_1 = db.query(MercuryAccount).filter(MercuryAccount.name == "Company A").first()
mercury_account_2 = db.query(MercuryAccount).filter(MercuryAccount.name == "Company B").first()

# Grant access to both account groups
user.mercury_accounts.extend([mercury_account_1, mercury_account_2])
db.commit()
```

## Security Considerations

1. **API Key Storage**: API keys are stored in the database. Consider encrypting them at rest.

2. **Password Hashing**: Use proper password hashing (bcrypt, scrypt, or Argon2) for user passwords.

3. **Access Control**: Implement proper authentication and authorization in your application.

4. **Database Security**: Secure your database with proper access controls and encryption.

## Migration from Single Account Setup

If you were previously using environment variables for a single Mercury account:

1. Run the migration script to add new tables
2. Create a MercuryAccount record with your existing API key
3. Update existing Account records to link to the new MercuryAccount
4. Remove the `MERCURY_API_KEY` environment variable
5. Test the sync process

## API Integration

Your application can now:
- Allow users to log in and see only their authorized account groups
- Display accounts and transactions grouped by Mercury account
- Provide different levels of access (read-only vs admin)
- Support multiple companies or business units with separate Mercury accounts

## Troubleshooting

### Common Issues

1. **No accounts syncing**: Check that MercuryAccount records have `is_active=True` and `sync_enabled=True`

2. **API key errors**: Verify API keys are correct and have proper permissions

3. **Missing account associations**: Ensure existing accounts have been linked to Mercury account groups

4. **Permission errors**: Check user-Mercury account associations in the `user_mercury_accounts` table

### Logging

The sync script provides detailed logging for each Mercury account group, making it easier to identify which accounts are failing and why.
