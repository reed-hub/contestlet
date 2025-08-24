-- Multi-Tier Role System Migration - SQLite Version
-- Run this on LOCAL SQLite development database

-- =====================================================
-- SQLITE MIGRATION: ROLE SYSTEM IMPLEMENTATION
-- =====================================================

BEGIN TRANSACTION;

-- =====================================================
-- 1. USERS TABLE UPDATES (SQLite doesn't support ADD COLUMN IF NOT EXISTS)
-- =====================================================

-- Check if role column exists, if not add it
PRAGMA table_info(users);

-- Add role system columns to existing users table
ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'user';
ALTER TABLE users ADD COLUMN is_verified BOOLEAN DEFAULT 0;
ALTER TABLE users ADD COLUMN created_by_user_id INTEGER REFERENCES users(id);
ALTER TABLE users ADD COLUMN role_assigned_at DATETIME DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE users ADD COLUMN role_assigned_by INTEGER REFERENCES users(id);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_created_by ON users(created_by_user_id);
CREATE INDEX IF NOT EXISTS idx_users_role_assigned_by ON users(role_assigned_by);

-- =====================================================
-- 2. SPONSOR PROFILES TABLE
-- =====================================================

CREATE TABLE IF NOT EXISTS sponsor_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    company_name VARCHAR(255) NOT NULL,
    website_url VARCHAR(500),
    logo_url VARCHAR(500),
    contact_email VARCHAR(255),
    contact_phone VARCHAR(50),
    industry VARCHAR(100),
    description TEXT,
    is_verified BOOLEAN DEFAULT 0,
    verification_document_url VARCHAR(500),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id)
);

-- Add indexes for sponsor profiles
CREATE INDEX IF NOT EXISTS idx_sponsor_profiles_user_id ON sponsor_profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_sponsor_profiles_company_name ON sponsor_profiles(company_name);
CREATE INDEX IF NOT EXISTS idx_sponsor_profiles_verified ON sponsor_profiles(is_verified);

-- =====================================================
-- 3. CONTESTS TABLE UPDATES
-- =====================================================

-- Add role system columns to existing contests table
ALTER TABLE contests ADD COLUMN created_by_user_id INTEGER REFERENCES users(id);
ALTER TABLE contests ADD COLUMN sponsor_profile_id INTEGER REFERENCES sponsor_profiles(id);
ALTER TABLE contests ADD COLUMN is_approved BOOLEAN DEFAULT 1; -- Default true for backward compatibility
ALTER TABLE contests ADD COLUMN approved_by_user_id INTEGER REFERENCES users(id);
ALTER TABLE contests ADD COLUMN approved_at DATETIME;

-- Add indexes for contests
CREATE INDEX IF NOT EXISTS idx_contests_created_by_user ON contests(created_by_user_id);
CREATE INDEX IF NOT EXISTS idx_contests_sponsor_profile ON contests(sponsor_profile_id);
CREATE INDEX IF NOT EXISTS idx_contests_approved ON contests(is_approved);
CREATE INDEX IF NOT EXISTS idx_contests_approved_by ON contests(approved_by_user_id);

-- =====================================================
-- 4. ROLE AUDIT TABLE
-- =====================================================

CREATE TABLE IF NOT EXISTS role_audit (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    old_role VARCHAR(20),
    new_role VARCHAR(20) NOT NULL,
    changed_by_user_id INTEGER REFERENCES users(id),
    reason TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Add indexes for role audit
CREATE INDEX IF NOT EXISTS idx_role_audit_user_id ON role_audit(user_id);
CREATE INDEX IF NOT EXISTS idx_role_audit_changed_by ON role_audit(changed_by_user_id);
CREATE INDEX IF NOT EXISTS idx_role_audit_created_at ON role_audit(created_at);

-- =====================================================
-- 5. CONTEST APPROVAL AUDIT TABLE
-- =====================================================

CREATE TABLE IF NOT EXISTS contest_approval_audit (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contest_id INTEGER NOT NULL REFERENCES contests(id),
    action VARCHAR(20) NOT NULL, -- 'approved', 'rejected', 'pending'
    approved_by_user_id INTEGER REFERENCES users(id),
    reason TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Add indexes for contest approval audit
CREATE INDEX IF NOT EXISTS idx_contest_approval_contest_id ON contest_approval_audit(contest_id);
CREATE INDEX IF NOT EXISTS idx_contest_approval_approved_by ON contest_approval_audit(approved_by_user_id);
CREATE INDEX IF NOT EXISTS idx_contest_approval_action ON contest_approval_audit(action);

-- =====================================================
-- 6. DATA MIGRATION FOR EXISTING RECORDS
-- =====================================================

-- Set admin role for known admin phone number
UPDATE users 
SET role = 'admin', 
    is_verified = 1,
    role_assigned_at = CURRENT_TIMESTAMP
WHERE phone = '+18187958204';

-- Set all existing contests as approved (backward compatibility)
UPDATE contests 
SET is_approved = 1,
    approved_at = CURRENT_TIMESTAMP
WHERE is_approved IS NULL;

-- Create initial role audit entries for existing users
INSERT INTO role_audit (user_id, old_role, new_role, reason, created_at)
SELECT 
    id,
    'user',
    role,
    'Initial role assignment during migration',
    CURRENT_TIMESTAMP
FROM users
WHERE role != 'user';

COMMIT;

-- =====================================================
-- 7. VERIFICATION QUERIES
-- =====================================================

-- Verify migration success
SELECT 'MIGRATION VERIFICATION' as status;

-- Show role distribution
SELECT 
    'ROLE DISTRIBUTION' as info,
    role,
    COUNT(*) as count
FROM users
GROUP BY role
ORDER BY role;

-- Show table counts
SELECT 
    'TABLE COUNTS' as info,
    'users' as table_name,
    COUNT(*) as count
FROM users
UNION ALL
SELECT 
    'TABLE COUNTS',
    'sponsor_profiles',
    COUNT(*)
FROM sponsor_profiles
UNION ALL
SELECT 
    'TABLE COUNTS',
    'contests',
    COUNT(*)
FROM contests
UNION ALL
SELECT 
    'TABLE COUNTS',
    'role_audit',
    COUNT(*)
FROM role_audit
UNION ALL
SELECT 
    'TABLE COUNTS',
    'contest_approval_audit',
    COUNT(*)
FROM contest_approval_audit;

-- Show updated table structure
PRAGMA table_info(users);
PRAGMA table_info(contests);

SELECT 'SQLITE ROLE SYSTEM MIGRATION COMPLETE' as final_status;
