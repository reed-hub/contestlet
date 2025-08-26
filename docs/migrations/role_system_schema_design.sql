-- Multi-Tier Role System - Database Schema Design
-- Phase 1: Foundation schema changes for Admin, Sponsor, User roles

-- =====================================================
-- 1. USERS TABLE UPDATES
-- =====================================================

-- Add role system columns to existing users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR(20) NOT NULL DEFAULT 'user';
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_verified BOOLEAN DEFAULT false;
ALTER TABLE users ADD COLUMN IF NOT EXISTS created_by_user_id INTEGER REFERENCES users(id);
ALTER TABLE users ADD COLUMN IF NOT EXISTS role_assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
ALTER TABLE users ADD COLUMN IF NOT EXISTS role_assigned_by INTEGER REFERENCES users(id);

-- Add role validation constraint
ALTER TABLE users DROP CONSTRAINT IF EXISTS valid_roles;
ALTER TABLE users ADD CONSTRAINT valid_roles CHECK (role IN ('admin', 'sponsor', 'user'));

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_created_by ON users(created_by_user_id);
CREATE INDEX IF NOT EXISTS idx_users_role_assigned_by ON users(role_assigned_by);

-- =====================================================
-- 2. SPONSOR PROFILES TABLE
-- =====================================================

CREATE TABLE IF NOT EXISTS sponsor_profiles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    company_name VARCHAR(255) NOT NULL,
    website_url VARCHAR(500),
    logo_url VARCHAR(500),
    contact_email VARCHAR(255),
    contact_phone VARCHAR(50),
    industry VARCHAR(100),
    description TEXT,
    is_verified BOOLEAN DEFAULT false,
    verification_document_url VARCHAR(500),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
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
ALTER TABLE contests ADD COLUMN IF NOT EXISTS created_by_user_id INTEGER REFERENCES users(id);
ALTER TABLE contests ADD COLUMN IF NOT EXISTS sponsor_profile_id INTEGER REFERENCES sponsor_profiles(id);
ALTER TABLE contests ADD COLUMN IF NOT EXISTS is_approved BOOLEAN DEFAULT true; -- Default true for backward compatibility
ALTER TABLE contests ADD COLUMN IF NOT EXISTS approved_by_user_id INTEGER REFERENCES users(id);
ALTER TABLE contests ADD COLUMN IF NOT EXISTS approved_at TIMESTAMP WITH TIME ZONE;

-- Add indexes for contests
CREATE INDEX IF NOT EXISTS idx_contests_created_by_user ON contests(created_by_user_id);
CREATE INDEX IF NOT EXISTS idx_contests_sponsor_profile ON contests(sponsor_profile_id);
CREATE INDEX IF NOT EXISTS idx_contests_approved ON contests(is_approved);
CREATE INDEX IF NOT EXISTS idx_contests_approved_by ON contests(approved_by_user_id);

-- =====================================================
-- 4. ROLE AUDIT TABLE (New)
-- =====================================================

CREATE TABLE IF NOT EXISTS role_audit (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    old_role VARCHAR(20),
    new_role VARCHAR(20) NOT NULL,
    changed_by_user_id INTEGER REFERENCES users(id),
    reason TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add indexes for role audit
CREATE INDEX IF NOT EXISTS idx_role_audit_user_id ON role_audit(user_id);
CREATE INDEX IF NOT EXISTS idx_role_audit_changed_by ON role_audit(changed_by_user_id);
CREATE INDEX IF NOT EXISTS idx_role_audit_created_at ON role_audit(created_at);

-- =====================================================
-- 5. CONTEST APPROVAL AUDIT TABLE (New)
-- =====================================================

CREATE TABLE IF NOT EXISTS contest_approval_audit (
    id SERIAL PRIMARY KEY,
    contest_id INTEGER NOT NULL REFERENCES contests(id),
    action VARCHAR(20) NOT NULL, -- 'approved', 'rejected', 'pending'
    approved_by_user_id INTEGER REFERENCES users(id),
    reason TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add indexes for contest approval audit
CREATE INDEX IF NOT EXISTS idx_contest_approval_contest_id ON contest_approval_audit(contest_id);
CREATE INDEX IF NOT EXISTS idx_contest_approval_approved_by ON contest_approval_audit(approved_by_user_id);
CREATE INDEX IF NOT EXISTS idx_contest_approval_action ON contest_approval_audit(action);

-- =====================================================
-- 6. DATA MIGRATION FOR EXISTING RECORDS
-- =====================================================

-- Migrate existing admin users (based on current admin system)
-- Note: This will need to be customized based on current admin identification method
UPDATE users 
SET role = 'admin', 
    is_verified = true,
    role_assigned_at = NOW()
WHERE phone IN (
    -- Add current admin phone numbers here
    '+18187958204'  -- Replace with actual admin phone numbers
);

-- Set all existing contests as approved (backward compatibility)
UPDATE contests 
SET is_approved = true,
    approved_at = NOW()
WHERE is_approved IS NULL;

-- =====================================================
-- 7. VERIFICATION QUERIES
-- =====================================================

-- Verify schema changes
SELECT 
    'users' as table_name,
    COUNT(*) as total_records,
    COUNT(CASE WHEN role = 'admin' THEN 1 END) as admin_count,
    COUNT(CASE WHEN role = 'sponsor' THEN 1 END) as sponsor_count,
    COUNT(CASE WHEN role = 'user' THEN 1 END) as user_count
FROM users
UNION ALL
SELECT 
    'sponsor_profiles' as table_name,
    COUNT(*) as total_records,
    NULL, NULL, NULL
FROM sponsor_profiles
UNION ALL
SELECT 
    'contests' as table_name,
    COUNT(*) as total_records,
    COUNT(CASE WHEN is_approved = true THEN 1 END) as approved_count,
    COUNT(CASE WHEN is_approved = false THEN 1 END) as pending_count,
    NULL
FROM contests;

-- Show new table structures
SELECT 
    table_name,
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name IN ('users', 'sponsor_profiles', 'contests', 'role_audit', 'contest_approval_audit')
    AND table_schema = 'public'
ORDER BY table_name, ordinal_position;
