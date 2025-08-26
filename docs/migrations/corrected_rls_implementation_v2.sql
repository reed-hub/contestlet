-- =====================================================
-- CORRECTED RLS IMPLEMENTATION FOR CONTESTLET SUPABASE - V2
-- =====================================================
-- Updated RLS policies for Contestlet's actual Supabase schema
-- Based on actual database structure from schema check
-- Handles existing policies gracefully
-- =====================================================

-- =====================================================
-- PHASE 1: PREPARATION AND CLEANUP
-- =====================================================

-- Drop existing policies to start fresh (only if they exist)
DO $$
BEGIN
    -- Users table policies
    IF EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'users' AND policyname = 'Users can view own profile') THEN
        DROP POLICY "Users can view own profile" ON public.users;
    END IF;
    
    IF EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'users' AND policyname = 'Users can update own profile') THEN
        DROP POLICY "Users can update own profile" ON public.users;
    END IF;
    
    IF EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'users' AND policyname = 'Users can insert own profile') THEN
        DROP POLICY "Users can insert own profile" ON public.users;
    END IF;
    
    IF EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'users' AND policyname = 'Admins can manage all users') THEN
        DROP POLICY "Admins can manage all users" ON public.users;
    END IF;
    
    -- Contests table policies
    IF EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'contests' AND policyname = 'Public can view active contests') THEN
        DROP POLICY "Public can view active contests" ON public.contests;
    END IF;
    
    IF EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'contests' AND policyname = 'Users can view active contests') THEN
        DROP POLICY "Users can view active contests" ON public.contests;
    END IF;
    
    IF EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'contests' AND policyname = 'Admins can manage all contests') THEN
        DROP POLICY "Admins can manage all contests" ON public.contests;
    END IF;
    
    IF EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'contests' AND policyname = 'Users can create contests') THEN
        DROP POLICY "Users can create contests" ON public.contests;
    END IF;
    
    -- Entries table policies
    IF EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'entries' AND policyname = 'Users can view own entries') THEN
        DROP POLICY "Users can view own entries" ON public.entries;
    END IF;
    
    IF EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'entries' AND policyname = 'Users can create own entries') THEN
        DROP POLICY "Users can create own entries" ON public.entries;
    END IF;
    
    IF EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'entries' AND policyname = 'Admins can view all entries') THEN
        DROP POLICY "Admins can view all entries" ON public.entries;
    END IF;
    
    -- Other table policies (drop if they exist)
    IF EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'admin_profiles' AND policyname = 'Admins can manage admin profiles') THEN
        DROP POLICY "Admins can manage admin profiles" ON public.admin_profiles;
    END IF;
    
    IF EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'official_rules' AND policyname = 'Public can view official rules') THEN
        DROP POLICY "Public can view official rules" ON public.official_rules;
    END IF;
    
    IF EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'official_rules' AND policyname = 'Admins can manage official rules') THEN
        DROP POLICY "Admins can manage official rules" ON public.official_rules;
    END IF;
    
    IF EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'sms_templates' AND policyname = 'Admins can access SMS templates') THEN
        DROP POLICY "Admins can access SMS templates" ON public.sms_templates;
    END IF;
    
    IF EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'notifications' AND policyname = 'Users can view own notifications') THEN
        DROP POLICY "Users can view own notifications" ON public.notifications;
    END IF;
    
    IF EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'notifications' AND policyname = 'Users can update own notifications') THEN
        DROP POLICY "Users can update own notifications" ON public.notifications;
    END IF;
    
    IF EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'notifications' AND policyname = 'Admins can manage all notifications') THEN
        DROP POLICY "Admins can manage all notifications" ON public.notifications;
    END IF;
END $$;

-- Ensure RLS is enabled on all tables that exist
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.contests ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.entries ENABLE ROW LEVEL SECURITY;

-- Enable RLS on other tables if they exist
DO $$
BEGIN
    -- Check and enable RLS for admin_profiles if it exists
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'admin_profiles') THEN
        ALTER TABLE public.admin_profiles ENABLE ROW LEVEL SECURITY;
    END IF;
    
    -- Check and enable RLS for official_rules if it exists
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'official_rules') THEN
        ALTER TABLE public.official_rules ENABLE ROW LEVEL SECURITY;
    END IF;
    
    -- Check and enable RLS for sms_templates if it exists
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'sms_templates') THEN
        ALTER TABLE public.sms_templates ENABLE ROW LEVEL SECURITY;
    END IF;
    
    -- Check and enable RLS for notifications if it exists
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'notifications') THEN
        ALTER TABLE public.notifications ENABLE ROW LEVEL SECURITY;
    END IF;
END $$;

-- =====================================================
-- PHASE 2: HELPER FUNCTIONS FOR ROLE CHECKING
-- =====================================================

-- Function to get current user's role from JWT
-- Since your users table doesn't have a role field, we'll use admin_user_id from contests
CREATE OR REPLACE FUNCTION get_user_role()
RETURNS TEXT AS $$
BEGIN
    -- Check if user is admin by looking at admin_user_id in contests
    IF EXISTS (
        SELECT 1 FROM public.contests 
        WHERE admin_user_id = auth.jwt() ->> 'phone'
        LIMIT 1
    ) THEN
        RETURN 'admin';
    END IF;
    
    -- Default to user role
    RETURN 'user';
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to check if current user is admin
CREATE OR REPLACE FUNCTION is_admin()
RETURNS BOOLEAN AS $$
BEGIN
    RETURN get_user_role() = 'admin';
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to get current user ID from JWT
CREATE OR REPLACE FUNCTION get_current_user_id()
RETURNS INTEGER AS $$
BEGIN
    RETURN COALESCE(
        (auth.jwt() ->> 'sub')::INTEGER,
        0
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to get current user phone from JWT
CREATE OR REPLACE FUNCTION get_current_user_phone()
RETURNS TEXT AS $$
BEGIN
    RETURN auth.jwt() ->> 'phone';
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =====================================================
-- PHASE 3: USERS TABLE POLICIES
-- =====================================================

-- Users can view their own profile
CREATE POLICY "Users can view own profile" ON public.users
    FOR SELECT USING (
        id = get_current_user_id()
        OR phone = get_current_user_phone()
    );

-- Users can update their own profile
CREATE POLICY "Users can update own profile" ON public.users
    FOR UPDATE USING (
        id = get_current_user_id()
        OR phone = get_current_user_phone()
    );

-- Users can insert their own profile during registration
CREATE POLICY "Users can insert own profile" ON public.users
    FOR INSERT WITH CHECK (
        id = get_current_user_id() OR 
        phone = get_current_user_phone()
    );

-- Admins can manage all users
CREATE POLICY "Admins can manage all users" ON public.users
    FOR ALL USING (is_admin());

-- =====================================================
-- PHASE 4: CONTESTS TABLE POLICIES
-- =====================================================

-- Public can view active contests
CREATE POLICY "Public can view active contests" ON public.contests
    FOR SELECT USING (active = true);

-- Users can view active contests (authenticated)
CREATE POLICY "Users can view active contests" ON public.contests
    FOR SELECT USING (
        active = true AND 
        auth.jwt() IS NOT NULL
    );

-- Admins can manage all contests
CREATE POLICY "Admins can manage all contests" ON public.contests
    FOR ALL USING (is_admin());

-- Users can create contests (will be limited by application logic)
CREATE POLICY "Users can create contests" ON public.contests
    FOR INSERT WITH CHECK (
        auth.jwt() IS NOT NULL
    );

-- =====================================================
-- PHASE 5: ENTRIES TABLE POLICIES
-- =====================================================

-- Users can view their own entries
CREATE POLICY "Users can view own entries" ON public.entries
    FOR SELECT USING (
        user_id = get_current_user_id()
        OR EXISTS (
            SELECT 1 FROM public.users u
            WHERE u.id = entries.user_id
            AND u.phone = get_current_user_phone()
        )
    );

-- Users can create their own entries
CREATE POLICY "Users can create own entries" ON public.entries
    FOR INSERT WITH CHECK (
        user_id = get_current_user_id()
        OR EXISTS (
            SELECT 1 FROM public.users u
            WHERE u.id = entries.user_id
            AND u.phone = get_current_user_phone()
        )
    );

-- Admins can view all entries
CREATE POLICY "Admins can view all entries" ON public.entries
    FOR ALL USING (is_admin());

-- =====================================================
-- PHASE 6: CONDITIONAL TABLE POLICIES
-- =====================================================

-- Admin Profiles (if table exists)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'admin_profiles') THEN
        -- Only admins can access admin profiles
        EXECUTE 'CREATE POLICY "Admins can manage admin profiles" ON public.admin_profiles FOR ALL USING (is_admin())';
    END IF;
END $$;

-- Official Rules (if table exists)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'official_rules') THEN
        -- Public can view official rules for active contests
        EXECUTE 'CREATE POLICY "Public can view official rules" ON public.official_rules FOR SELECT USING (EXISTS (SELECT 1 FROM public.contests c WHERE c.id = official_rules.contest_id AND c.active = true))';
        
        -- Admins can manage all official rules
        EXECUTE 'CREATE POLICY "Admins can manage official rules" ON public.official_rules FOR ALL USING (is_admin())';
    END IF;
END $$;

-- SMS Templates (if table exists)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'sms_templates') THEN
        -- Only admins can access SMS templates
        EXECUTE 'CREATE POLICY "Admins can access SMS templates" ON public.sms_templates FOR ALL USING (is_admin())';
    END IF;
END $$;

-- Notifications (if table exists)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'notifications') THEN
        -- Users can view their own notifications
        EXECUTE 'CREATE POLICY "Users can view own notifications" ON public.notifications FOR SELECT USING (user_id = get_current_user_id())';
        
        -- Users can update their own notifications
        EXECUTE 'CREATE POLICY "Users can update own notifications" ON public.notifications FOR UPDATE USING (user_id = get_current_user_id())';
        
        -- Admins can manage all notifications
        EXECUTE 'CREATE POLICY "Admins can manage all notifications" ON public.notifications FOR ALL USING (is_admin())';
    END IF;
END $$;

-- =====================================================
-- PHASE 7: PERFORMANCE OPTIMIZATION
-- =====================================================

-- Create indexes for RLS performance
CREATE INDEX IF NOT EXISTS idx_contests_active ON public.contests(active) WHERE active = true;
CREATE INDEX IF NOT EXISTS idx_entries_user_id ON public.entries(user_id);
CREATE INDEX IF NOT EXISTS idx_entries_contest_id ON public.entries(contest_id);
CREATE INDEX IF NOT EXISTS idx_users_phone ON public.users(phone);

-- =====================================================
-- PHASE 8: GRANT PERMISSIONS
-- =====================================================

-- Revoke default permissions
REVOKE ALL ON public.users FROM PUBLIC;
REVOKE ALL ON public.contests FROM PUBLIC;
REVOKE ALL ON public.entries FROM PUBLIC;

-- Grant specific permissions to authenticated users
GRANT SELECT ON public.contests TO authenticated;
GRANT SELECT, INSERT ON public.entries TO authenticated;
GRANT SELECT ON public.users TO authenticated;

-- Grant usage on sequences
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO authenticated;

-- =====================================================
-- PHASE 9: VALIDATION AND TESTING
-- =====================================================

-- Test query to validate RLS setup
SELECT 
    'Corrected RLS Implementation Complete' as status,
    'Database security updated for actual Contestlet schema' as message,
    COUNT(*) as total_policies
FROM pg_policies 
WHERE schemaname = 'public';

-- Verify all tables have RLS enabled
SELECT 
    tablename,
    CASE WHEN rowsecurity THEN '🔒 SECURED' ELSE '⚠️ UNSECURED' END as rls_status
FROM pg_tables 
WHERE schemaname = 'public' 
AND tablename IN ('users', 'contests', 'entries');

-- =====================================================
-- COMPLETION MESSAGE
-- =====================================================

SELECT 
    '✅ CORRECTED RLS IMPLEMENTATION COMPLETE!' as status,
    'Database security updated for actual Supabase schema' as message,
    'Test your application with different user roles' as next_steps;
