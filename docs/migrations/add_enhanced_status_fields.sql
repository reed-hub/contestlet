-- Enhanced Contest Status System Migration
-- Adds enhanced status workflow fields to support 8-state contest system
-- Run this migration to enable the Enhanced Contest Status System

-- =====================================================
-- 1. ADD ENHANCED STATUS WORKFLOW FIELDS
-- =====================================================

-- Add enhanced status workflow fields to contests table
ALTER TABLE contests ADD COLUMN IF NOT EXISTS submitted_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE contests ADD COLUMN IF NOT EXISTS approved_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE contests ADD COLUMN IF NOT EXISTS rejected_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE contests ADD COLUMN IF NOT EXISTS rejection_reason TEXT;
ALTER TABLE contests ADD COLUMN IF NOT EXISTS approval_message TEXT;
ALTER TABLE contests ADD COLUMN IF NOT EXISTS created_by_user_id INTEGER;

-- Add foreign key constraint for created_by_user_id (if users table exists)
-- Note: This may fail in SQLite if users table doesn't exist, which is OK
-- ALTER TABLE contests ADD CONSTRAINT fk_contests_created_by_user_id 
--     FOREIGN KEY (created_by_user_id) REFERENCES users(id);

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
  AND status NOT IN ('draft', 'awaiting_approval', 'rejected')
  AND created_at IS NOT NULL;

-- =====================================================
-- 4. VALIDATE MIGRATION
-- =====================================================

-- Check that all contests have creator references
-- SELECT COUNT(*) as contests_without_creator FROM contests WHERE created_by_user_id IS NULL;

-- Check status distribution
-- SELECT status, COUNT(*) as count FROM contests GROUP BY status ORDER BY count DESC;

-- Check enhanced fields
-- SELECT 
--     COUNT(*) as total_contests,
--     COUNT(submitted_at) as with_submitted_at,
--     COUNT(approved_at) as with_approved_at,
--     COUNT(rejected_at) as with_rejected_at
-- FROM contests;

-- =====================================================
-- MIGRATION COMPLETE
-- =====================================================

-- The Enhanced Contest Status System is now ready!
-- 
-- New fields added:
-- - submitted_at: When contest was submitted for approval
-- - approved_at: When admin approved the contest  
-- - rejected_at: When admin rejected the contest
-- - rejection_reason: Admin's reason for rejection
-- - approval_message: Admin's approval notes
-- - created_by_user_id: Reference to contest creator
--
-- Enhanced status workflow now supports:
-- - draft: Sponsor working copy
-- - awaiting_approval: Submitted for admin review
-- - rejected: Admin rejected with feedback
-- - upcoming: Approved, scheduled for future
-- - active: Currently accepting entries
-- - ended: Time expired, no winner selected
-- - complete: Winner selected and announced
-- - cancelled: Administratively cancelled
