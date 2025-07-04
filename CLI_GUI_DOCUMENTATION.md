# Command-Line GUI for Mercury Bank Sync Service

## Overview

The CLI GUI provides a text-based interface for managing the Mercury Bank sync service when the web GUI is not available or not installed. This is particularly useful for:

- Server environments without web interface
- Headless installations
- Remote administration via SSH
- Development and debugging
- Backup administration interface

## Access Control

**No Authentication Required**: The CLI GUI assumes that if you have access to run it, you have administrative privileges. This is because:

- CLI access requires database connection credentials (`DATABASE_URL`)
- Access to the file system where the application is installed
- Typically used in trusted environments (servers, development machines)

The CLI GUI automatically determines admin user context for logging and informational purposes, but does not restrict functionality based on user roles.

## Features

### 🖥️ **System Status**
- Database connection status
- User count and Mercury account information
- Transaction statistics
- Environment variable configuration
- Sync activity overview

### 🏦 **Mercury Account Management**
- List all Mercury accounts with status
- Add new Mercury accounts with encrypted API keys
- Edit existing account settings
- Enable/disable accounts
- Test API connectivity

### 👥 **User Management**
- List users with their assigned roles
- Create new users with role assignment
- Manage user roles (add/remove roles)
- Reset user passwords
- Lock/unlock user accounts

### 📊 **Sync Activity Monitoring**
- View recent transactions
- Check Mercury account sync status
- Monitor log files
- Track sync performance

### 🔧 **Database Tools**
- Run database migrations
- Check database schema integrity
- View database statistics
- Basic backup utilities

## Access Methods

### Method 1: Via dev.sh (Recommended for Development)
```bash
./dev.sh cli-gui
```

### Method 2: Direct Docker Execution
```bash
docker-compose exec mercury-sync python cli_gui.py
```

### Method 3: Standalone Launcher
```bash
cd sync_app
./launch_cli.sh
```

### Method 4: Direct Execution (Inside Container)
```bash
# If already inside the sync container
python cli_gui.py
```

## Requirements

- Running Mercury Bank sync service
- Database connectivity
- Admin credentials for management functions

## Authentication

Most administrative functions require authentication:
- **System Status**: No authentication required
- **Mercury Accounts**: Admin/Super-admin required
- **User Management**: Admin/Super-admin required  
- **Database Tools**: Admin/Super-admin required
- **Sync Activity**: No authentication required

## User Interface

### Color-Coded Output
- **🟢 Green**: Success messages and confirmations
- **🔴 Red**: Error messages and failures
- **🟡 Yellow**: Warnings and important notices
- **🔵 Blue**: Information and prompts
- **🟣 Purple**: Headers and titles

### Navigation
- Use number keys to select menu options
- Enter commands as prompted
- Use `Ctrl+C` to exit at any time
- Most operations return to the previous menu

## Common Tasks

### Adding a Mercury Account
1. Select `2. Manage Mercury Accounts`
2. Choose `2. Add Mercury account`
3. Enter account name, API key, and configuration
4. Account is automatically encrypted and stored

### Creating a User
1. Select `3. Manage Users`
2. Choose `2. Add user`
3. Enter user details and assign roles
4. User can immediately log in to web interface

### Checking System Health
1. Select `1. System Status`
2. Review database connectivity
3. Check user and account counts
4. Verify environment configuration

### Managing User Roles
1. Select `3. Manage Users`
2. Choose `3. Manage user roles`
3. Select user by ID
4. Add or remove roles as needed

## Security Features

- **Encrypted API Keys**: All Mercury API keys are encrypted before storage
- **Password Masking**: Passwords are hidden during input
- **Admin Authentication**: Sensitive operations require admin login
- **Graceful Exit**: Safe shutdown with Ctrl+C handling

## Error Handling

The CLI GUI includes comprehensive error handling:
- Database connection failures
- Authentication errors
- Invalid input validation
- API key encryption/decryption issues
- Transaction rollback on errors

## Troubleshooting

### Connection Issues
```bash
# Check if services are running
docker-compose ps

# Restart services if needed
./dev.sh rebuild-dev
```

### Authentication Problems
- Ensure you have admin or super-admin role
- Check username/password combination
- Verify user account is not locked

### Missing Features
If certain menu options are missing:
- Verify you have the latest version
- Check user permissions
- Ensure database is properly migrated

## Integration with Web GUI

The CLI GUI and Web GUI share the same database and functionality:
- Users created in CLI appear in web interface
- Mercury accounts are synchronized
- Role changes take effect immediately
- All data is consistent between interfaces

## Advantages over Web GUI

1. **Lower Resource Usage**: No web server overhead
2. **SSH Friendly**: Works over terminal connections
3. **Scriptable**: Can be automated with expect scripts
4. **Always Available**: Independent of web service status
5. **Faster Navigation**: Keyboard-only operation

## File Locations

- **Main Script**: `sync_app/cli_gui.py`
- **Launcher**: `sync_app/launch_cli.sh`
- **Dev Command**: `./dev.sh cli-gui`

## Future Enhancements

Planned features for future versions:
- Bulk user import/export
- Advanced log analysis
- API testing utilities
- Backup/restore functionality
- Configuration wizards
- Performance monitoring

---

**Note**: This CLI GUI is designed to complement, not replace, the web interface. Use it for administrative tasks, troubleshooting, and environments where the web GUI is not suitable.
