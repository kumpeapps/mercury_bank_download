# User Access Management and Signup Control

This update adds comprehensive user access management and signup control features to the Mercury Bank web application.

## New Features

### 1. Mercury Account Access Management
- **Share Mercury accounts**: Give other users access to your Mercury accounts
- **Manage user permissions**: Add or remove users from Mercury accounts
- **Security**: Only users with existing access can manage permissions
- **Protection**: Cannot remove the last user with access to prevent lockout

### 2. Signup Control
- **Admin control**: Admins can enable/disable user registration
- **Auto-detection**: If the `users` table is a database view, signups are automatically disabled
- **Graceful handling**: Users see appropriate messages when registration is disabled

### 3. Admin Interface
- **System settings**: Centralized configuration management
- **Easy toggles**: Simple on/off switches for boolean settings
- **Secure access**: Only admin users can access settings

## Database Changes

### New Table: `system_settings`
```sql
CREATE TABLE system_settings (
    `key` VARCHAR(100) NOT NULL PRIMARY KEY,
    `value` TEXT NULL,
    `description` TEXT NULL,
    `is_editable` BOOLEAN DEFAULT TRUE,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

### Default Settings
- `signup_enabled`: Controls whether new user registration is allowed
  - Automatically set to `false` if `users` table is a view
  - Default `true` for regular tables

## Setup Instructions

### 1. Update Database Schema
Run the schema update script:
```bash
python update_schema.py
```

Or manually apply the SQL:
```bash
mysql -u user -p mercury_bank < add_system_settings.sql
```

### 2. Create Admin User
Ensure at least one user has admin privileges:
```sql
UPDATE users SET is_admin = TRUE WHERE username = 'your_admin_username';
```

### 3. Restart Web Application
Restart the Flask application to load the new features.

## Usage

### For Regular Users

#### Sharing Mercury Account Access
1. Go to **Accounts** page
2. Click the gear icon next to a Mercury account
3. Select **Manage Access**
4. Add users by selecting them from the dropdown
5. Remove users by clicking the **Remove** button

### For Administrators

#### Managing System Settings
1. Access **Settings** from the sidebar (only visible to admins)
2. Toggle **signup_enabled** to control user registration
3. Click **Save Settings** to apply changes

#### Checking User Table Type
The system automatically detects if the `users` table is a view and disables signups accordingly. This is useful when user authentication is managed externally.

## Security Considerations

### Access Control
- Only users with existing access to a Mercury account can manage its permissions
- Admin privileges are required to access system settings
- Cannot remove the last user with access to prevent lockout

### Data Protection
- All user access changes are logged through database timestamps
- Mercury account credentials remain secure and are not exposed during access management

## API Endpoints

### New Routes
- `GET/POST /manage_mercury_access/<mercury_account_id>`: Manage user access to Mercury accounts
- `GET/POST /admin/settings`: Admin interface for system settings

### Updated Routes
- `GET/POST /register`: Now checks if signup is enabled before allowing registration
- `GET /login`: Passes signup status to template for conditional display

## Template Updates

### New Templates
- `manage_mercury_access.html`: Interface for managing Mercury account access
- `admin_settings.html`: Admin interface for system settings

### Updated Templates
- `accounts.html`: Added "Manage Access" option to Mercury account dropdown
- `base.html`: Added "Settings" link for admin users
- `login.html`: Conditional display of registration link

## Error Handling

### Graceful Degradation
- If system settings table doesn't exist, defaults to allowing signups
- If database connection fails during settings check, registration remains enabled
- Clear error messages for access denied scenarios

### User Experience
- Informative flash messages for all actions
- Confirmation dialogs for destructive actions
- Disabled buttons/options when actions aren't available

## Troubleshooting

### Common Issues

#### "Registration is disabled" message
- Check if `users` table is a view: `SHOW FULL TABLES LIKE 'users';`
- Admin can enable signups in Settings page
- Check `system_settings` table for `signup_enabled` value

#### Cannot access admin settings
- Ensure user has `is_admin = TRUE` in database
- Check if user is logged in with admin account

#### Cannot manage Mercury account access
- Ensure user has existing access to the Mercury account
- Check the `user_mercury_account_association` table for relationships

### Database Queries for Debugging

```sql
-- Check admin users
SELECT username, is_admin FROM users WHERE is_admin = TRUE;

-- Check system settings
SELECT * FROM system_settings;

-- Check Mercury account access
SELECT u.username, ma.name 
FROM users u
JOIN user_mercury_account_association uma ON u.id = uma.user_id
JOIN mercury_accounts ma ON uma.mercury_account_id = ma.id;

-- Check if users table is a view
SELECT TABLE_TYPE FROM information_schema.TABLES 
WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'users';
```

## Future Enhancements

### Potential Features
- Role-based permissions (read-only vs. full access)
- User invitation system via email
- Audit logging for access changes
- Bulk user management
- External authentication integration (LDAP, OAuth)

This implementation provides a solid foundation for user access management while maintaining security and ease of use.

## Admin User Management

### First User Auto-Admin

Starting with this update, the **first user to register** in the system is **automatically granted admin privileges**. This ensures that there's always at least one admin user who can manage the system.

#### How It Works

1. When a user registers, the system checks if they are the first user (user count = 0)
2. If they are the first user, their `UserSettings.is_admin` field is automatically set to `True`
3. The registration confirmation message indicates when admin privileges have been granted

### Managing Admin Users

#### Using Command Line Tools

Several command-line utilities are provided for admin user management:

**Create First Admin User** (if no users exist):
```bash
# Using the development helper
./dev.sh create-admin

# Or directly in the container
docker-compose exec web-app python admin_user.py create
```

**Promote Existing User to Admin:**
```bash
./dev.sh promote-admin <username>
```

**List All Admin Users:**
```bash
./dev.sh list-admin
```

**Ensure First User is Admin (Migration):**
```bash
./dev.sh ensure-admin
```

This migration script will:
1. Check if any admin users exist
2. If no admin users exist, promote the first user (oldest by ID) to admin
3. Create UserSettings if needed

### Admin User Scripts

**admin_user.py** - Comprehensive admin user management:
- `create` - Create first admin user
- `promote <username>` - Promote user to admin
- `list` - List all admin users

**ensure_first_admin.py** - Migration utility to ensure at least one admin exists
