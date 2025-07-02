-- Migration to add system_settings table
-- This allows for configuration of application settings like signup control

CREATE TABLE IF NOT EXISTS system_settings (
    `key` VARCHAR(100) NOT NULL PRIMARY KEY,
    `value` TEXT NULL,
    `description` TEXT NULL,
    `is_editable` BOOLEAN DEFAULT TRUE,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insert default settings
-- Check if users table is a view to determine default signup behavior
SET @is_users_view = (
    SELECT IF(
        (SELECT TABLE_TYPE FROM information_schema.TABLES 
         WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'users') = 'VIEW',
        'false',
        'true'
    )
);

-- Insert signup_enabled setting with appropriate default
INSERT IGNORE INTO system_settings (`key`, `value`, `description`, `is_editable`)
VALUES 
    ('signup_enabled', @is_users_view, 'Whether new user registration is enabled', TRUE);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_system_settings_is_editable ON system_settings(is_editable);
