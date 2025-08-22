-- Add image_url and host_name columns to contests table
-- Run this on staging/production Supabase database

-- Add image_url column for contest hero images
ALTER TABLE contests 
ADD COLUMN IF NOT EXISTS image_url VARCHAR;

-- Add host_name column for contest organizer/sponsor
ALTER TABLE contests 
ADD COLUMN IF NOT EXISTS host_name VARCHAR;

-- Verify the columns were added
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'contests' 
AND column_name IN ('image_url', 'host_name');
