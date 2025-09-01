-- Enhanced Contest Status System Migration - SQLite Compatible
-- Adds enhanced status workflow fields to support 8-state contest system

-- =====================================================
-- 1. ADD ENHANCED STATUS WORKFLOW FIELDS
-- =====================================================

-- Add enhanced status workflow fields to contests table (SQLite compatible)
ALTER TABLE contests ADD COLUMN submitted_at DATETIME;
ALTER TABLE contests ADD COLUMN approved_at DATETIME;
ALTER TABLE contests ADD COLUMN rejected_at DATETIME;
ALTER TABLE contests ADD COLUMN rejection_reason TEXT;
ALTER TABLE contests ADD COLUMN approval_message TEXT;
ALTER TABLE contests ADD COLUMN created_by_user_id INTEGER;

-- Add status column if it doesn't exist (SQLite doesn't support IF NOT EXISTS for columns)
-- This may fail if column already exists, which is OK
-- ALTER TABLE contests ADD COLUMN status VARCHAR(20) DEFAULT 'upcoming';

-- =====================================================
-- 2. ADD INDEXES FOR PERFORMANCE
-- =====================================================

-- Add indexes for enhanced status system queries
CREATE INDEX IF NOT EXISTS idx_contests_submitted_at ON contests(submitted_at);
CREATE INDEX IF NOT EXISTS idx_contests_approved_at ON contests(approved_at);
CREATE INDEX IF NOT EXISTS idx_contests_rejected_at ON contests(rejected_at);
CREATE INDEX IF NOT EXISTS idx_contests_created_by_user_id ON contests(created_by_user_id);

-- Ensure status field is indexed (may already exist)
CREATE INDEX IF NOT EXISTS idx_contests_status ON contests(status);

-- =====================================================
-- 3. MIGRATE EXISTING DATA
-- =====================================================

-- Update existing contests to have proper creator references
-- Set created_by_user_id to 1 (admin) for existing contests without creator
UPDATE contests 
SET created_by_user_id = 1 
WHERE created_by_user_id IS NULL;

-- Set approved_at for contests that are already published
-- Assume contests with status not in draft/awaiting_approval/rejected are approved
UPDATE contests 
SET approved_at = created_at 
WHERE approved_at IS NULL 
  AND created_at IS NOT NULL;

-- Set default status for contests without status
UPDATE contests 
SET status = 'upcoming' 
WHERE status IS NULL;

-- =====================================================
-- MIGRATION COMPLETE
-- =====================================================

-- Check results
SELECT 'Migration completed successfully' as result;
SELECT COUNT(*) as total_contests FROM contests;
SELECT COUNT(*) as contests_with_creator FROM contests WHERE created_by_user_id IS NOT NULL;
