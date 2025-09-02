-- Multiple Winners Feature Database Schema
-- This migration adds support for multiple winners per contest

-- 1. Add new fields to contests table for multiple winners support
ALTER TABLE contests ADD COLUMN winner_count INTEGER DEFAULT 1 NOT NULL;
ALTER TABLE contests ADD COLUMN prize_tiers JSONB DEFAULT NULL;

-- Add comments for new fields
COMMENT ON COLUMN contests.winner_count IS 'Number of winners for this contest (1-50)';
COMMENT ON COLUMN contests.prize_tiers IS 'Optional structured prize information as JSON array';

-- 2. Create contest_winners table for managing multiple winners
CREATE TABLE contest_winners (
    id SERIAL PRIMARY KEY,
    contest_id INTEGER NOT NULL REFERENCES contests(id) ON DELETE CASCADE,
    entry_id INTEGER NOT NULL REFERENCES entries(id) ON DELETE CASCADE,
    winner_position INTEGER NOT NULL CHECK (winner_position >= 1 AND winner_position <= 50),
    prize_description TEXT,
    selected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    notified_at TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    claimed_at TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    
    -- Constraints
    CONSTRAINT unique_contest_entry UNIQUE(contest_id, entry_id),
    CONSTRAINT unique_contest_position UNIQUE(contest_id, winner_position)
);

-- Add indexes for performance
CREATE INDEX idx_contest_winners_contest_id ON contest_winners(contest_id);
CREATE INDEX idx_contest_winners_entry_id ON contest_winners(entry_id);
CREATE INDEX idx_contest_winners_position ON contest_winners(contest_id, winner_position);
CREATE INDEX idx_contest_winners_selected_at ON contest_winners(selected_at);

-- Add comments
COMMENT ON TABLE contest_winners IS 'Stores multiple winners for contests with their positions and prizes';
COMMENT ON COLUMN contest_winners.winner_position IS 'Position of winner (1st, 2nd, 3rd place, etc.)';
COMMENT ON COLUMN contest_winners.prize_description IS 'Specific prize for this winner position';
COMMENT ON COLUMN contest_winners.selected_at IS 'When this winner was selected';
COMMENT ON COLUMN contest_winners.notified_at IS 'When winner notification was sent';
COMMENT ON COLUMN contest_winners.claimed_at IS 'When winner claimed their prize';

-- 3. Data migration: Move existing single winners to new table
INSERT INTO contest_winners (contest_id, entry_id, winner_position, selected_at)
SELECT 
    id as contest_id,
    winner_entry_id as entry_id,
    1 as winner_position,
    COALESCE(winner_selected_at, NOW()) as selected_at
FROM contests 
WHERE winner_entry_id IS NOT NULL;

-- 4. Add check constraint to ensure winner_count matches actual winners
-- This will be enforced at the application level for now

-- 5. Example prize_tiers JSON structure:
/*
{
  "tiers": [
    {
      "position": 1,
      "prize": "$100 Gift Card",
      "description": "First place winner receives a $100 Amazon gift card"
    },
    {
      "position": 2,
      "prize": "$50 Gift Card", 
      "description": "Second place winner receives a $50 Amazon gift card"
    },
    {
      "position": 3,
      "prize": "$25 Gift Card",
      "description": "Third place winner receives a $25 Amazon gift card"
    }
  ],
  "total_value": 175,
  "currency": "USD"
}
*/

-- 6. Add validation function for prize_tiers JSON
CREATE OR REPLACE FUNCTION validate_prize_tiers(prize_tiers JSONB, winner_count INTEGER)
RETURNS BOOLEAN AS $$
BEGIN
    -- If prize_tiers is NULL, it's valid
    IF prize_tiers IS NULL THEN
        RETURN TRUE;
    END IF;
    
    -- Check if it has the required structure
    IF NOT (prize_tiers ? 'tiers' AND jsonb_typeof(prize_tiers->'tiers') = 'array') THEN
        RETURN FALSE;
    END IF;
    
    -- Check if number of tiers matches winner_count
    IF jsonb_array_length(prize_tiers->'tiers') != winner_count THEN
        RETURN FALSE;
    END IF;
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- Note: For SQLite compatibility, we'll handle validation in the application layer
