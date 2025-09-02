-- Migration: Add timezone preference fields to users table
-- Date: January 2025
-- Purpose: Extend timezone preferences from admin-only to all user roles

-- Add timezone columns to users table
ALTER TABLE users ADD COLUMN timezone VARCHAR(50) DEFAULT NULL;
ALTER TABLE users ADD COLUMN timezone_auto_detect BOOLEAN DEFAULT true;

-- Add index for timezone queries (optional, for performance)
CREATE INDEX IF NOT EXISTS idx_users_timezone ON users(timezone);

-- Update existing users to have default timezone preferences
UPDATE users SET 
    timezone = 'UTC',
    timezone_auto_detect = true
WHERE timezone IS NULL;

-- SQLite doesn't support COMMENT ON COLUMN, but the column purposes are:
-- timezone: IANA timezone identifier (e.g., America/New_York). NULL means use system default (UTC)
-- timezone_auto_detect: Whether to auto-detect timezone from browser. If false, use explicit timezone setting
