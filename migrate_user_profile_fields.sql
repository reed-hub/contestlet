-- Migration: Add personal profile fields to users table
-- Date: 2025-08-27
-- Description: Add full_name, email, bio, and updated_at columns to support comprehensive user profiles

-- Add new columns to users table
ALTER TABLE users 
ADD COLUMN full_name VARCHAR(255),
ADD COLUMN email VARCHAR(255),
ADD COLUMN bio VARCHAR(1000),
ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();

-- Create index on email for faster lookups
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- Update existing users to have updated_at = created_at initially
UPDATE users SET updated_at = created_at WHERE updated_at IS NULL;

-- Add trigger to automatically update updated_at on row changes (PostgreSQL)
-- Note: This is PostgreSQL specific. For SQLite, the onupdate parameter in SQLAlchemy handles this.
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for users table
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Verify the migration
SELECT 
    column_name, 
    data_type, 
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'users' 
    AND column_name IN ('full_name', 'email', 'bio', 'updated_at')
ORDER BY column_name;

-- Show sample of updated table structure
SELECT 
    id, 
    phone, 
    role, 
    full_name, 
    email, 
    bio, 
    created_at, 
    updated_at 
FROM users 
LIMIT 3;
