-- Multiple Winners Feature Database Migration (SQLite Compatible)
-- This migration adds support for multiple winners per contest

-- 1. Add new fields to contests table for multiple winners support
ALTER TABLE contests ADD COLUMN winner_count INTEGER DEFAULT 1 NOT NULL;
ALTER TABLE contests ADD COLUMN prize_tiers TEXT DEFAULT NULL; -- JSON as TEXT for SQLite

-- 2. Create contest_winners table for managing multiple winners
CREATE TABLE contest_winners (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contest_id INTEGER NOT NULL,
    entry_id INTEGER NOT NULL,
    winner_position INTEGER NOT NULL CHECK (winner_position >= 1 AND winner_position <= 50),
    prize_description TEXT,
    selected_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    notified_at DATETIME DEFAULT NULL,
    claimed_at DATETIME DEFAULT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    -- Foreign key constraints
    FOREIGN KEY (contest_id) REFERENCES contests(id) ON DELETE CASCADE,
    FOREIGN KEY (entry_id) REFERENCES entries(id) ON DELETE CASCADE,
    
    -- Unique constraints
    UNIQUE(contest_id, entry_id),
    UNIQUE(contest_id, winner_position)
);

-- Create indexes for performance
CREATE INDEX idx_contest_winners_contest_id ON contest_winners(contest_id);
CREATE INDEX idx_contest_winners_entry_id ON contest_winners(entry_id);
CREATE INDEX idx_contest_winners_position ON contest_winners(contest_id, winner_position);
CREATE INDEX idx_contest_winners_selected_at ON contest_winners(selected_at);

-- 3. Data migration: Move existing single winners to new table
INSERT INTO contest_winners (contest_id, entry_id, winner_position, selected_at)
SELECT 
    id as contest_id,
    winner_entry_id as entry_id,
    1 as winner_position,
    COALESCE(winner_selected_at, CURRENT_TIMESTAMP) as selected_at
FROM contests 
WHERE winner_entry_id IS NOT NULL;

-- 4. Update existing contests to have winner_count = 1 where they have winners
UPDATE contests 
SET winner_count = 1 
WHERE winner_entry_id IS NOT NULL;

-- Example prize_tiers JSON structure (stored as TEXT in SQLite):
-- {
--   "tiers": [
--     {"position": 1, "prize": "$100 Gift Card", "description": "First place winner"},
--     {"position": 2, "prize": "$50 Gift Card", "description": "Second place winner"},
--     {"position": 3, "prize": "$25 Gift Card", "description": "Third place winner"}
--   ],
--   "total_value": 175,
--   "currency": "USD"
-- }
