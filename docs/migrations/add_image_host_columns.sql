-- Add image_url and sponsor_url columns to contests table
-- Run this on staging/production Supabase database
-- Note: sponsor_name already exists in official_rules table

-- Add image_url column for contest hero images
ALTER TABLE contests 
ADD COLUMN IF NOT EXISTS image_url VARCHAR;

-- Add sponsor_url column for sponsor website
ALTER TABLE contests 
ADD COLUMN IF NOT EXISTS sponsor_url VARCHAR;

-- Remove host_name column if it exists (replaced by sponsor_url)
-- Note: This may fail if column doesn't exist, which is fine
ALTER TABLE contests 
DROP COLUMN IF EXISTS host_name;

-- Verify the columns were added
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'contests' 
AND column_name IN ('image_url', 'sponsor_url');
