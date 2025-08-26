-- Multi-Tier Role System - RLS Policies Update
-- This updates existing RLS policies to work with the new role system

-- =====================================================
-- DISABLE EXISTING RLS POLICIES (TEMPORARILY)
-- =====================================================

-- Drop existing policies to recreate them with role support
DROP POLICY IF EXISTS "Users can view own profile" ON users;
DROP POLICY IF EXISTS "Users can update own profile" ON users;
DROP POLICY IF EXISTS "Users can insert own profile" ON users;
DROP POLICY IF EXISTS "Public can view active contests" ON contests;
DROP POLICY IF EXISTS "Admins can manage contests" ON contests;
DROP POLICY IF EXISTS "Users can view own entries" ON entries;
DROP POLICY IF EXISTS "Users can create own entries" ON entries;
DROP POLICY IF EXISTS "Admins can view all entries" ON entries;
DROP POLICY IF EXISTS "Users can view own notifications" ON notifications;
DROP POLICY IF EXISTS "Users can update own notifications" ON notifications;
DROP POLICY IF EXISTS "Admins can view all notifications" ON notifications;
DROP POLICY IF EXISTS "Public can view official rules for active contests" ON official_rules;
DROP POLICY IF EXISTS "Admins can manage official rules" ON official_rules;
DROP POLICY IF EXISTS "Only admins can access SMS templates" ON sms_templates;
DROP POLICY IF EXISTS "Allow authenticated access to admin profiles" ON admin_profiles;

-- =====================================================
-- HELPER FUNCTIONS FOR ROLE CHECKING
-- =====================================================

-- Function to get current user's role from JWT
CREATE OR REPLACE FUNCTION get_user_role()
RETURNS TEXT AS $$
BEGIN
    RETURN COALESCE(
        (auth.jwt() ->> 'role')::TEXT,
        'user'
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to check if current user is admin
CREATE OR REPLACE FUNCTION is_admin()
RETURNS BOOLEAN AS $$
BEGIN
    RETURN get_user_role() = 'admin';
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to check if current user is sponsor
CREATE OR REPLACE FUNCTION is_sponsor()
RETURNS BOOLEAN AS $$
BEGIN
    RETURN get_user_role() IN ('sponsor', 'admin');
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

-- =====================================================
-- USERS TABLE POLICIES
-- =====================================================

-- Users can view their own profile
CREATE POLICY "Users can view own profile" ON users
    FOR SELECT USING (
        id = get_current_user_id()
    );

-- Users can update their own profile (limited fields)
CREATE POLICY "Users can update own profile" ON users
    FOR UPDATE USING (
        id = get_current_user_id()
    );

-- Users can insert their own profile during registration
CREATE POLICY "Users can insert own profile" ON users
    FOR INSERT WITH CHECK (
        id = get_current_user_id() OR 
        is_admin() -- Admins can create users
    );

-- Admins can manage all users
CREATE POLICY "Admins can manage all users" ON users
    FOR ALL USING (is_admin());

-- Sponsors can view basic user info for their contest entries
CREATE POLICY "Sponsors can view contest participants" ON users
    FOR SELECT USING (
        is_sponsor() AND EXISTS (
            SELECT 1 FROM entries e
            JOIN contests c ON e.contest_id = c.id
            WHERE e.user_id = users.id
            AND c.created_by_user_id = get_current_user_id()
        )
    );

-- =====================================================
-- SPONSOR PROFILES TABLE POLICIES
-- =====================================================

-- Sponsors can manage their own profile
CREATE POLICY "Sponsors can manage own profile" ON sponsor_profiles
    FOR ALL USING (
        user_id = get_current_user_id() AND is_sponsor()
    );

-- Admins can manage all sponsor profiles
CREATE POLICY "Admins can manage all sponsor profiles" ON sponsor_profiles
    FOR ALL USING (is_admin());

-- Public can view verified sponsor profiles (for contest display)
CREATE POLICY "Public can view verified sponsor profiles" ON sponsor_profiles
    FOR SELECT USING (is_verified = true);

-- =====================================================
-- CONTESTS TABLE POLICIES
-- =====================================================

-- Public can view approved contests
CREATE POLICY "Public can view approved contests" ON contests
    FOR SELECT USING (is_approved = true);

-- Sponsors can manage their own contests
CREATE POLICY "Sponsors can manage own contests" ON contests
    FOR ALL USING (
        is_sponsor() AND created_by_user_id = get_current_user_id()
    );

-- Sponsors can create new contests (will be unapproved by default)
CREATE POLICY "Sponsors can create contests" ON contests
    FOR INSERT WITH CHECK (
        is_sponsor() AND created_by_user_id = get_current_user_id()
    );

-- Admins can manage all contests
CREATE POLICY "Admins can manage all contests" ON contests
    FOR ALL USING (is_admin());

-- Users can view approved contests (duplicate of public policy for clarity)
CREATE POLICY "Users can view approved contests" ON contests
    FOR SELECT USING (
        is_approved = true AND 
        auth.jwt() IS NOT NULL -- Must be authenticated
    );

-- =====================================================
-- ENTRIES TABLE POLICIES
-- =====================================================

-- Users can view their own entries
CREATE POLICY "Users can view own entries" ON entries
    FOR SELECT USING (
        user_id = get_current_user_id()
    );

-- Users can create their own entries
CREATE POLICY "Users can create own entries" ON entries
    FOR INSERT WITH CHECK (
        user_id = get_current_user_id()
    );

-- Sponsors can view entries for their contests
CREATE POLICY "Sponsors can view contest entries" ON entries
    FOR SELECT USING (
        is_sponsor() AND EXISTS (
            SELECT 1 FROM contests c
            WHERE c.id = entries.contest_id
            AND c.created_by_user_id = get_current_user_id()
        )
    );

-- Admins can view all entries
CREATE POLICY "Admins can view all entries" ON entries
    FOR ALL USING (is_admin());

-- =====================================================
-- NOTIFICATIONS TABLE POLICIES
-- =====================================================

-- Users can view their own notifications
CREATE POLICY "Users can view own notifications" ON notifications
    FOR SELECT USING (
        user_id = get_current_user_id()
    );

-- Users can update their own notifications (mark as read, etc.)
CREATE POLICY "Users can update own notifications" ON notifications
    FOR UPDATE USING (
        user_id = get_current_user_id()
    );

-- Sponsors can create notifications for their contest participants
CREATE POLICY "Sponsors can create contest notifications" ON notifications
    FOR INSERT WITH CHECK (
        is_sponsor() AND EXISTS (
            SELECT 1 FROM entries e
            JOIN contests c ON e.contest_id = c.id
            WHERE e.user_id = notifications.user_id
            AND c.created_by_user_id = get_current_user_id()
        )
    );

-- Admins can manage all notifications
CREATE POLICY "Admins can manage all notifications" ON notifications
    FOR ALL USING (is_admin());

-- =====================================================
-- OFFICIAL RULES TABLE POLICIES
-- =====================================================

-- Public can view official rules for approved contests
CREATE POLICY "Public can view official rules for approved contests" ON official_rules
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM contests c
            WHERE c.id = official_rules.contest_id
            AND c.is_approved = true
        )
    );

-- Sponsors can manage official rules for their contests
CREATE POLICY "Sponsors can manage own contest rules" ON official_rules
    FOR ALL USING (
        is_sponsor() AND EXISTS (
            SELECT 1 FROM contests c
            WHERE c.id = official_rules.contest_id
            AND c.created_by_user_id = get_current_user_id()
        )
    );

-- Admins can manage all official rules
CREATE POLICY "Admins can manage all official rules" ON official_rules
    FOR ALL USING (is_admin());

-- =====================================================
-- SMS TEMPLATES TABLE POLICIES
-- =====================================================

-- Sponsors can manage SMS templates for their contests
CREATE POLICY "Sponsors can manage own contest SMS templates" ON sms_templates
    FOR ALL USING (
        is_sponsor() AND EXISTS (
            SELECT 1 FROM contests c
            WHERE c.id = sms_templates.contest_id
            AND c.created_by_user_id = get_current_user_id()
        )
    );

-- Admins can manage all SMS templates
CREATE POLICY "Admins can manage all SMS templates" ON sms_templates
    FOR ALL USING (is_admin());

-- =====================================================
-- ADMIN PROFILES TABLE POLICIES
-- =====================================================

-- Admins can manage admin profiles
CREATE POLICY "Admins can manage admin profiles" ON admin_profiles
    FOR ALL USING (is_admin());

-- =====================================================
-- ROLE AUDIT TABLE POLICIES
-- =====================================================

-- Users can view their own role change history
CREATE POLICY "Users can view own role audit" ON role_audit
    FOR SELECT USING (
        user_id = get_current_user_id()
    );

-- Admins can view all role audit records
CREATE POLICY "Admins can view all role audit" ON role_audit
    FOR SELECT USING (is_admin());

-- Only admins can create role audit records
CREATE POLICY "Admins can create role audit records" ON role_audit
    FOR INSERT WITH CHECK (is_admin());

-- =====================================================
-- CONTEST APPROVAL AUDIT TABLE POLICIES
-- =====================================================

-- Sponsors can view approval history for their contests
CREATE POLICY "Sponsors can view own contest approval audit" ON contest_approval_audit
    FOR SELECT USING (
        is_sponsor() AND EXISTS (
            SELECT 1 FROM contests c
            WHERE c.id = contest_approval_audit.contest_id
            AND c.created_by_user_id = get_current_user_id()
        )
    );

-- Admins can manage all contest approval audit records
CREATE POLICY "Admins can manage all contest approval audit" ON contest_approval_audit
    FOR ALL USING (is_admin());

-- =====================================================
-- VERIFICATION QUERIES
-- =====================================================

-- Verify all policies are created
SELECT 
    schemaname,
    tablename,
    policyname,
    permissive,
    roles,
    cmd
FROM pg_policies 
WHERE schemaname = 'public'
ORDER BY tablename, policyname;

-- Verify RLS is enabled on all tables
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
        'official_rules', 'sms_templates', 'admin_profiles',
        'sponsor_profiles', 'role_audit', 'contest_approval_audit'
    )
ORDER BY tablename;

-- Summary
SELECT 
    'RLS POLICY UPDATE COMPLETE' as status,
    COUNT(*) as total_policies
FROM pg_policies 
WHERE schemaname = 'public';
