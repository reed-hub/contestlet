-- Manual Entry Fields Migration
-- Adds support for admin manual entry creation with tracking fields

-- Add new columns to entries table
ALTER TABLE entries ADD COLUMN source VARCHAR(50) DEFAULT 'web_app' NOT NULL;
ALTER TABLE entries ADD COLUMN created_by_admin_id INTEGER REFERENCES users(id);
ALTER TABLE entries ADD COLUMN admin_notes TEXT;

-- Create indexes for performance
CREATE INDEX idx_entries_source ON entries(source);
CREATE INDEX idx_entries_admin ON entries(created_by_admin_id);
CREATE INDEX idx_entries_source_admin ON entries(source, created_by_admin_id);

-- Update existing entries to have 'web_app' source
UPDATE entries SET source = 'web_app' WHERE source IS NULL;

-- Add comments for documentation
COMMENT ON COLUMN entries.source IS 'Entry source tracking: web_app, manual_admin, phone_call, event, etc.';
COMMENT ON COLUMN entries.created_by_admin_id IS 'Admin user ID who created manual entry (NULL for regular entries)';
COMMENT ON COLUMN entries.admin_notes IS 'Admin notes for manual entries (max 500 characters recommended)';

-- Verify the changes
SELECT 
    column_name, 
    data_type, 
    is_nullable, 
    column_default
FROM information_schema.columns 
WHERE table_name = 'entries' 
    AND column_name IN ('source', 'created_by_admin_id', 'admin_notes')
ORDER BY column_name;
