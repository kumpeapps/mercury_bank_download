-- MySQL initialization script for Mercury Bank application
-- This script will be executed when the MySQL container starts for the first time

-- Ensure we're using the correct database
USE mercury_bank;

-- Set timezone
SET time_zone = '+00:00';

-- IMPORTANT: All database operations should be done through SQLAlchemy
-- This file is only for initial MySQL-specific configuration
-- Tables, schema changes, and data migrations are all handled by SQLAlchemy

-- DO NOT add SQL schema definitions or data insertions here
-- Instead, use the appropriate SQLAlchemy models and migrations

-- Application will automatically:
-- 1. Create all tables via SQLAlchemy models
-- 2. Initialize system settings via Python code
-- 3. Handle all migrations through SQLAlchemy-based migration system
-- 4. Manage admin users and permissions

-- For more information, see the documentation in docs/ directory
