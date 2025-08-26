-- Migration: Add missing contact_name field to sponsor_profiles table
-- Date: 2025-08-25
-- Purpose: Fix frontend issue where sponsor name field cannot be saved

-- Add contact_name field if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'sponsor_profiles' 
        AND column_name = 'contact_name'
    ) THEN
        ALTER TABLE sponsor_profiles 
        ADD COLUMN contact_name VARCHAR(255);
        
        -- Add index for performance
        CREATE INDEX idx_sponsor_profiles_contact_name 
        ON sponsor_profiles(contact_name);
        
        RAISE NOTICE 'Added contact_name field to sponsor_profiles table';
    ELSE
        RAISE NOTICE 'contact_name field already exists in sponsor_profiles table';
    END IF;
END $$;

-- Verify the change
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'sponsor_profiles' 
AND column_name IN ('contact_name', 'contact_email', 'contact_phone')
ORDER BY column_name;
