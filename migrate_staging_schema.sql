-- Migration script to add missing columns to staging database
-- Run this on the staging Supabase database

-- Smart Location System fields
ALTER TABLE contests ADD COLUMN IF NOT EXISTS location_type VARCHAR(20) DEFAULT 'united_states';
ALTER TABLE contests ADD COLUMN IF NOT EXISTS selected_states JSON;
ALTER TABLE contests ADD COLUMN IF NOT EXISTS radius_address VARCHAR(500);
ALTER TABLE contests ADD COLUMN IF NOT EXISTS radius_miles INTEGER;
ALTER TABLE contests ADD COLUMN IF NOT EXISTS radius_latitude FLOAT;
ALTER TABLE contests ADD COLUMN IF NOT EXISTS radius_longitude FLOAT;

-- Winner tracking fields
ALTER TABLE contests ADD COLUMN IF NOT EXISTS winner_entry_id INTEGER;
ALTER TABLE contests ADD COLUMN IF NOT EXISTS winner_phone VARCHAR;
ALTER TABLE contests ADD COLUMN IF NOT EXISTS winner_selected_at TIMESTAMP WITH TIME ZONE;

-- Timezone and admin metadata
ALTER TABLE contests ADD COLUMN IF NOT EXISTS created_timezone VARCHAR(50);
ALTER TABLE contests ADD COLUMN IF NOT EXISTS admin_user_id VARCHAR(50);

-- Campaign import metadata
ALTER TABLE contests ADD COLUMN IF NOT EXISTS campaign_metadata JSON;

-- Contest configuration fields
ALTER TABLE contests ADD COLUMN IF NOT EXISTS contest_type VARCHAR(50);
ALTER TABLE contests ADD COLUMN IF NOT EXISTS entry_method VARCHAR(50);
ALTER TABLE contests ADD COLUMN IF NOT EXISTS winner_selection_method VARCHAR(50);
ALTER TABLE contests ADD COLUMN IF NOT EXISTS minimum_age INTEGER;
ALTER TABLE contests ADD COLUMN IF NOT EXISTS max_entries_per_person INTEGER;
ALTER TABLE contests ADD COLUMN IF NOT EXISTS total_entry_limit INTEGER;

-- Additional contest details
ALTER TABLE contests ADD COLUMN IF NOT EXISTS consolation_offer TEXT;
ALTER TABLE contests ADD COLUMN IF NOT EXISTS geographic_restrictions TEXT;
ALTER TABLE contests ADD COLUMN IF NOT EXISTS contest_tags JSON;
ALTER TABLE contests ADD COLUMN IF NOT EXISTS promotion_channels JSON;

-- Visual branding and sponsor information
ALTER TABLE contests ADD COLUMN IF NOT EXISTS image_url VARCHAR;
ALTER TABLE contests ADD COLUMN IF NOT EXISTS sponsor_url VARCHAR;

-- Create SMS templates table if it doesn't exist
CREATE TABLE IF NOT EXISTS sms_templates (
    id SERIAL PRIMARY KEY,
    contest_id INTEGER NOT NULL REFERENCES contests(id) ON DELETE CASCADE,
    template_type VARCHAR(50) NOT NULL,
    message_content TEXT NOT NULL,
    variables JSON,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create admin_profiles table if it doesn't exist
CREATE TABLE IF NOT EXISTS admin_profiles (
    id SERIAL PRIMARY KEY,
    admin_user_id VARCHAR(50) NOT NULL UNIQUE,
    timezone VARCHAR(50) DEFAULT 'UTC',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Verify the migration
SELECT 
    table_name,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns 
WHERE table_name IN ('contests', 'sms_templates', 'admin_profiles')
ORDER BY table_name, ordinal_position;
