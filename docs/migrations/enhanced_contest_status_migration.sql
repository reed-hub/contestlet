# Enhanced Contest Status System Migration
# Adds unified status field and migrates existing data

-- =====================================================
-- 1. ADD NEW STATUS FIELD
-- =====================================================

-- Add the new status column with default value
ALTER TABLE contests ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'upcoming';

-- Add index for performance
CREATE INDEX IF NOT EXISTS idx_contests_status ON contests(status);

-- =====================================================
-- 2. MIGRATE EXISTING DATA
-- =====================================================

-- Migrate existing contests to new status values based on current state
UPDATE contests SET status = CASE 
    -- If not approved by admin, set to awaiting approval
    WHEN is_approved = false THEN 'awaiting_approval'
    
    -- If winner selected, contest is complete
    WHEN winner_selected_at IS NOT NULL THEN 'complete'
    
    -- If end time has passed and no winner, contest ended
    WHEN end_time < NOW() AND winner_selected_at IS NULL THEN 'ended'
    
    -- If start time is in future, contest is upcoming
    WHEN start_time > NOW() THEN 'upcoming'
    
    -- If between start and end time, contest is active
    WHEN start_time <= NOW() AND end_time >= NOW() AND winner_selected_at IS NULL THEN 'active'
    
    -- Default fallback
    ELSE 'upcoming'
END;

-- =====================================================
-- 3. ADD STATUS TRANSITION AUDIT TABLE
-- =====================================================

CREATE TABLE IF NOT EXISTS contest_status_audit (
    id SERIAL PRIMARY KEY,
    contest_id INTEGER NOT NULL REFERENCES contests(id) ON DELETE CASCADE,
    old_status VARCHAR(20),
    new_status VARCHAR(20) NOT NULL,
    changed_by_user_id INTEGER REFERENCES users(id),
    reason TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Indexes
    INDEX idx_status_audit_contest (contest_id),
    INDEX idx_status_audit_status (new_status),
    INDEX idx_status_audit_user (changed_by_user_id),
    INDEX idx_status_audit_created (created_at)
);

-- =====================================================
-- 4. UPDATE CONSTRAINTS AND VALIDATION
-- =====================================================

-- Add check constraint for valid status values
ALTER TABLE contests ADD CONSTRAINT IF NOT EXISTS chk_contest_status 
CHECK (status IN ('draft', 'awaiting_approval', 'upcoming', 'active', 'ended', 'complete', 'rejected'));

-- =====================================================
-- 5. LEGACY FIELD CLEANUP
-- =====================================================

-- The is_approved and active fields are no longer used
-- All logic now uses the enhanced status field exclusively

-- =====================================================
-- 6. DATA VERIFICATION QUERIES
-- =====================================================

-- Verify migration results
-- SELECT status, COUNT(*) as count FROM contests GROUP BY status ORDER BY status;
-- SELECT status, created_by_user_id, COUNT(*) FROM contests GROUP BY status, created_by_user_id ORDER BY status;
