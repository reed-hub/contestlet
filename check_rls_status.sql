-- Check RLS (Row Level Security) status across all tables
-- Run this on staging and production to see current security state

-- Check if RLS is enabled on tables
SELECT 
    schemaname,
    tablename,
    rowsecurity as rls_enabled,
    CASE 
        WHEN rowsecurity THEN '🔒 SECURE'
        ELSE '⚠️ UNSECURED'
    END as security_status
FROM pg_tables 
WHERE schemaname = 'public' 
    AND tablename IN (
        'users', 'contests', 'entries', 'notifications', 
        'official_rules', 'sms_templates', 'admin_profiles'
    )
ORDER BY tablename;

-- Check existing RLS policies
SELECT 
    schemaname,
    tablename,
    policyname,
    permissive,
    roles,
    cmd,
    qual,
    with_check
FROM pg_policies 
WHERE schemaname = 'public'
ORDER BY tablename, policyname;

-- Summary
SELECT 
    COUNT(*) as total_tables,
    SUM(CASE WHEN rowsecurity THEN 1 ELSE 0 END) as secured_tables,
    ROUND(
        (SUM(CASE WHEN rowsecurity THEN 1 ELSE 0 END) * 100.0 / COUNT(*)), 1
    ) as security_percentage
FROM pg_tables 
WHERE schemaname = 'public' 
    AND tablename IN (
        'users', 'contests', 'entries', 'notifications', 
        'official_rules', 'sms_templates', 'admin_profiles'
    );
