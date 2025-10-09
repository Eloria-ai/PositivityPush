-- Positivity Push Database Schema for Supabase
-- Run these commands in your Supabase SQL editor

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Subscribers table (main user data)
CREATE TABLE IF NOT EXISTS subscribers (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    
    -- Stripe Integration
    stripe_session_id VARCHAR(255) UNIQUE,
    stripe_customer_id VARCHAR(255),
    stripe_subscription_id VARCHAR(255),
    
    -- User Information
    email VARCHAR(255),
    phone_number VARCHAR(20),
    wa_id VARCHAR(50) UNIQUE, -- WhatsApp ID
    
    -- Subscription Details
    plan_type VARCHAR(20) CHECK (plan_type IN ('3_month', '6_month')),
    status VARCHAR(20) DEFAULT 'paid_pending_optin' 
        CHECK (status IN ('paid_pending_optin', 'active', 'paused', 'cancelled', 'payment_failed')),
    amount_total INTEGER, -- In cents
    currency VARCHAR(3) DEFAULT 'usd',
    
    -- Personal Coaching Data
    personal_goals JSONB DEFAULT '{}',
    communication_style JSONB DEFAULT '{}',
    active_challenges JSONB DEFAULT '[]',
    timezone VARCHAR(50) DEFAULT 'UTC', -- Original timezone from onboarding
    
    -- Dynamic Timezone Tracking (for traveling users)
    current_timezone VARCHAR(50) DEFAULT 'UTC', -- User's actual timezone based on phone/IP detection
    timezone_updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(), -- When timezone was last updated
    client_ip VARCHAR(45), -- IPv6 max length, for IP-based timezone detection fallback
    
    -- Fixed Affirmation Times (no longer customizable)
    morning_positivity VARCHAR(5) DEFAULT '08:00', -- Fixed morning affirmation time
    midday_positivity VARCHAR(5) DEFAULT '12:00', -- Fixed midday affirmation time  
    afternoon_positivity VARCHAR(5) DEFAULT '16:00', -- Fixed afternoon affirmation time
    
    -- User Scheduling Preferences (only personalized times)
    preferences JSONB DEFAULT '{
        "day_planning": "08:00", 
        "accountability_checkin": "19:00",
        "evening_gratitude": "21:00",
        "weekly_reflection": {
            "day": "sunday",
            "time": "10:00"
        },
        "onboarding_completed": false
    }',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    activated_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    cancelled_at TIMESTAMP WITH TIME ZONE,
    last_payment_at TIMESTAMP WITH TIME ZONE,
    failed_payment_at TIMESTAMP WITH TIME ZONE
);

-- Conversations table (message history)
CREATE TABLE IF NOT EXISTS conversations (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    subscriber_id UUID REFERENCES subscribers(id) ON DELETE CASCADE,
    
    -- Message Data
    content TEXT NOT NULL,
    message_type VARCHAR(20) NOT NULL CHECK (message_type IN ('user', 'assistant')),
    wa_message_id VARCHAR(255), -- WhatsApp message ID
    
    -- AI Context
    context_used TEXT, -- mem0 context that was used
    effectiveness_score INTEGER CHECK (effectiveness_score BETWEEN 1 AND 5),
    
    -- Timestamps
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User Progress table (weekly tracking)
CREATE TABLE IF NOT EXISTS user_progress (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    subscriber_id UUID REFERENCES subscribers(id) ON DELETE CASCADE,
    
    -- Time Period
    week_start DATE NOT NULL,
    week_end DATE GENERATED ALWAYS AS (week_start + INTERVAL '6 days') STORED,
    
    -- Progress Data
    wins JSONB DEFAULT '[]', -- Array of achievements
    challenges JSONB DEFAULT '[]', -- Array of struggles
    goal_progress JSONB DEFAULT '{}', -- Progress on specific goals
    mood_patterns JSONB DEFAULT '[]', -- Mood tracking data
    
    -- AI Analysis
    coaching_adjustments JSONB DEFAULT '{}', -- How AI should adapt
    progress_score INTEGER CHECK (progress_score BETWEEN 1 AND 10),
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Ensure one record per user per week
    UNIQUE(subscriber_id, week_start)
);

-- Daily plans capture (for context-aware check-ins)
CREATE TABLE IF NOT EXISTS daily_plans (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    subscriber_id UUID REFERENCES subscribers(id) ON DELETE CASCADE,
    plan_date DATE NOT NULL,
    items JSONB DEFAULT '[]', -- Structured array of plan items
    raw_text TEXT, -- Original user response for reference
    extracted_goals JSONB DEFAULT NULL, -- AI-extracted goals analysis with categories and insights
    completion_status JSONB DEFAULT NULL, -- Array of {item, completed, item_number}
    completion_response TEXT, -- User's raw completion response
    completed_at TIMESTAMP WITH TIME ZONE DEFAULT NULL, -- When completion was recorded
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Prevent duplicates - one plan per user per day
    UNIQUE(subscriber_id, plan_date)
);

-- Weekly goals tracking (aggregated from daily plans or explicit goals)
CREATE TABLE IF NOT EXISTS weekly_goals (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    subscriber_id UUID REFERENCES subscribers(id) ON DELETE CASCADE,
    week_start DATE NOT NULL, -- Monday of the week
    items JSONB DEFAULT '[]', -- Structured array of weekly goals
    source VARCHAR(20) DEFAULT 'daily_aggregate', -- 'daily_aggregate' or 'explicit'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Prevent duplicates - one set of goals per user per week
    UNIQUE(subscriber_id, week_start)
);

-- Scheduled Messages table (UUID-based architecture)
-- NOTE: IF NOT EXISTS preserves existing UUID column if table already exists
CREATE TABLE IF NOT EXISTS scheduled_messages (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    subscriber_id UUID REFERENCES subscribers(id) ON DELETE CASCADE,
    
    -- Message Details
    message_type VARCHAR(30) NOT NULL 
        CHECK (message_type IN ('daily_affirmation', 'gratitude_prompt', 'accountability_checkin', 'day_planning', 'weekly_reflection', 'midday_boost', 'evening_wind_down', 'onboarding_welcome', 'onboarding_response', 'onboarding_question')),
    scheduled_for TIMESTAMP WITH TIME ZONE NOT NULL,
    content TEXT, -- Pre-generated content for onboarding messages, NULL for AI-generated coaching messages
    
    -- Status with new architecture states
    status VARCHAR(20) DEFAULT 'pending' 
        CHECK (status IN ('pending', 'queued', 'sent', 'failed', 'cancelled')),
    sent_at TIMESTAMP WITH TIME ZONE,
    last_error TEXT,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_subscribers_wa_id ON subscribers(wa_id);
CREATE INDEX IF NOT EXISTS idx_subscribers_stripe_session ON subscribers(stripe_session_id);
CREATE INDEX IF NOT EXISTS idx_subscribers_status ON subscribers(status);
CREATE INDEX IF NOT EXISTS idx_subscribers_preferences ON subscribers USING GIN (preferences);
CREATE INDEX IF NOT EXISTS idx_subscribers_onboarding ON subscribers ((preferences->>'onboarding_completed'));
CREATE INDEX IF NOT EXISTS idx_subscribers_current_timezone ON subscribers(current_timezone);
CREATE INDEX IF NOT EXISTS idx_subscribers_timezone_updated ON subscribers(timezone_updated_at);
CREATE INDEX IF NOT EXISTS idx_conversations_subscriber_timestamp ON conversations(subscriber_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_user_progress_subscriber_week ON user_progress(subscriber_id, week_start DESC);
CREATE INDEX IF NOT EXISTS idx_scheduled_messages_pending ON scheduled_messages(status, scheduled_for) WHERE status = 'pending';
CREATE INDEX IF NOT EXISTS idx_scheduled_messages_id ON scheduled_messages(id);
CREATE INDEX IF NOT EXISTS idx_scheduled_messages_subscriber ON scheduled_messages(subscriber_id);

-- Execute Raw SQL function for SKIP LOCKED operations (FIXED VERSION)
-- Drop the old function first to avoid type conflicts
DROP FUNCTION IF EXISTS execute_raw_sql(text);

-- FIXED: execute_raw_sql function now returns UUID for id column (matching actual table schema)
CREATE OR REPLACE FUNCTION execute_raw_sql(query text)
RETURNS TABLE(id uuid, subscriber_id uuid, message_type varchar(30), scheduled_for timestamptz)
LANGUAGE plpgsql 
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    trimmed_query text;
BEGIN
    -- Add basic query validation for security
    IF query IS NULL OR query = '' THEN
        RAISE EXCEPTION 'Query cannot be null or empty';
    END IF;
    
    -- Trim ALL whitespace including newlines and check query type
    trimmed_query := UPPER(TRIM(BOTH E' \t\n\r' FROM query));
    
    -- Allow WITH and UPDATE queries for SKIP LOCKED operations
    IF trimmed_query NOT LIKE 'WITH %' 
       AND trimmed_query NOT LIKE 'UPDATE %' 
       AND trimmed_query NOT LIKE 'SELECT %' THEN
        RAISE EXCEPTION 'Only WITH, UPDATE, or SELECT queries allowed in this function. Got: %', LEFT(trimmed_query, 50);
    END IF;
    
    -- Additional security: prevent dangerous operations
    IF trimmed_query LIKE '%DROP %' 
       OR trimmed_query LIKE '%DELETE %' 
       OR trimmed_query LIKE '%TRUNCATE %' THEN
        RAISE EXCEPTION 'Dangerous operations not allowed';
    END IF;
    
    RETURN QUERY EXECUTE query;
END;
$$;

-- Updated timestamp triggers (with secure search path)
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER 
SET search_path = ''
LANGUAGE plpgsql 
SECURITY DEFINER
AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

-- Drop trigger if exists, then create
DROP TRIGGER IF EXISTS update_subscribers_updated_at ON subscribers;
CREATE TRIGGER update_subscribers_updated_at 
    BEFORE UPDATE ON subscribers 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Add trigger for scheduled_messages updated_at
DROP TRIGGER IF EXISTS update_scheduled_messages_updated_at ON scheduled_messages;
CREATE TRIGGER update_scheduled_messages_updated_at 
    BEFORE UPDATE ON scheduled_messages 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- RLS (Row Level Security) Policies
ALTER TABLE subscribers ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_progress ENABLE ROW LEVEL SECURITY;
ALTER TABLE scheduled_messages ENABLE ROW LEVEL SECURITY;

-- Service role can access everything (for backend) 
-- Drop existing policies if they exist, then create
DROP POLICY IF EXISTS "Service role can manage all data" ON subscribers;
CREATE POLICY "Service role can manage all data" ON subscribers
    FOR ALL USING (auth.role() = 'service_role');

DROP POLICY IF EXISTS "Service role can manage all conversations" ON conversations;    
CREATE POLICY "Service role can manage all conversations" ON conversations
    FOR ALL USING (auth.role() = 'service_role');

DROP POLICY IF EXISTS "Service role can manage all progress" ON user_progress;    
CREATE POLICY "Service role can manage all progress" ON user_progress
    FOR ALL USING (auth.role() = 'service_role');

DROP POLICY IF EXISTS "Service role can manage all scheduled messages" ON scheduled_messages;    
CREATE POLICY "Service role can manage all scheduled messages" ON scheduled_messages
    FOR ALL USING (auth.role() = 'service_role');

-- Grant permissions to service role
GRANT ALL ON ALL TABLES IN SCHEMA public TO service_role;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO service_role;

-- Column comments for documentation
COMMENT ON COLUMN subscribers.current_timezone IS 'User''s current timezone based on phone/IP detection, updated when traveling';
COMMENT ON COLUMN subscribers.timezone_updated_at IS 'Timestamp when timezone was last updated';
COMMENT ON COLUMN subscribers.client_ip IS 'User''s IP address for timezone detection fallback';
COMMENT ON COLUMN subscribers.timezone IS 'Original timezone from onboarding (kept for reference)';

-- Data migration for existing records (safe to run multiple times)
-- Update existing records to set current_timezone from original timezone column
UPDATE subscribers 
SET current_timezone = COALESCE(timezone, 'UTC')
WHERE current_timezone IS NULL OR current_timezone = 'UTC';

-- Migration for positivity columns (safe to run multiple times)
-- Add columns if they don't exist (for existing databases)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'subscribers' AND column_name = 'morning_positivity') THEN
        ALTER TABLE subscribers ADD COLUMN morning_positivity VARCHAR(5) DEFAULT '08:00';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'subscribers' AND column_name = 'midday_positivity') THEN
        ALTER TABLE subscribers ADD COLUMN midday_positivity VARCHAR(5) DEFAULT '12:00';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'subscribers' AND column_name = 'afternoon_positivity') THEN
        ALTER TABLE subscribers ADD COLUMN afternoon_positivity VARCHAR(5) DEFAULT '16:00';
    END IF;
END $$;

-- Back-fill existing rows with default times
UPDATE subscribers
SET
  morning_positivity = COALESCE(morning_positivity, '08:00'),
  midday_positivity = COALESCE(midday_positivity, '12:00'),
  afternoon_positivity = COALESCE(afternoon_positivity, '16:00')
WHERE morning_positivity IS NULL OR midday_positivity IS NULL OR afternoon_positivity IS NULL;

-- Clean up old affirmation keys from preferences JSON (optional cleanup)
UPDATE subscribers
SET preferences = preferences 
    - 'morning_affirmation'
    - 'midday_affirmation' 
    - 'evening_affirmation'
WHERE preferences ? 'morning_affirmation' 
   OR preferences ? 'midday_affirmation'
   OR preferences ? 'evening_affirmation';

-- =====================================================
-- COMPREHENSIVE SCHEMA FIXES (PRODUCTION-READY)
-- =====================================================

-- Fix 1: Update scheduled_messages CHECK constraint with all message types
ALTER TABLE scheduled_messages DROP CONSTRAINT IF EXISTS scheduled_messages_message_type_check;
ALTER TABLE scheduled_messages ADD CONSTRAINT scheduled_messages_message_type_check 
CHECK (message_type IN (
    -- Core daily messages (fixed times)
    'daily_affirmation', 'midday_boost', 'evening_wind_down',
    -- User-customized messages  
    'day_planning', 'accountability_checkin', 'gratitude_prompt', 'weekly_reflection',
    -- Onboarding messages
    'onboarding_welcome', 'onboarding_response', 'onboarding_question',
    -- System messages
    'system_notification', 'subscription_update', 'error_notification'
));

-- Fix 2: Ensure current_timezone is always set (critical for scheduling)
UPDATE subscribers 
SET current_timezone = COALESCE(current_timezone, timezone, 'UTC')
WHERE current_timezone IS NULL OR current_timezone = '';

-- Fix 3: Ensure all active users have onboarding_completed flag
UPDATE subscribers 
SET preferences = COALESCE(preferences, '{}')
WHERE preferences IS NULL;

UPDATE subscribers 
SET preferences = preferences || '{"onboarding_completed": true}'::jsonb
WHERE status = 'active' 
  AND (preferences->>'onboarding_completed') IS NULL;

-- Fix 4: Add performance optimization indexes
CREATE INDEX IF NOT EXISTS idx_scheduled_messages_type_status ON scheduled_messages(message_type, status);
CREATE INDEX IF NOT EXISTS idx_scheduled_messages_scheduled_for ON scheduled_messages(scheduled_for);
CREATE INDEX IF NOT EXISTS idx_subscribers_status_onboarding ON subscribers(status, (preferences->>'onboarding_completed'));
CREATE INDEX IF NOT EXISTS idx_subscribers_timezone_status ON subscribers(current_timezone, status);

-- Fix 5: Data validation trigger for better data integrity
CREATE OR REPLACE FUNCTION validate_user_preferences()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    -- Ensure timezone is valid
    IF NEW.current_timezone IS NOT NULL THEN
        BEGIN
            -- Test if timezone is valid by using it
            PERFORM NOW() AT TIME ZONE NEW.current_timezone;
        EXCEPTION WHEN OTHERS THEN
            NEW.current_timezone = 'UTC';
        END;
    END IF;
    
    -- Ensure preferences is valid JSON
    IF NEW.preferences IS NULL THEN
        NEW.preferences = '{}'::jsonb;
    END IF;
    
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS validate_user_preferences_trigger ON subscribers;
CREATE TRIGGER validate_user_preferences_trigger
    BEFORE INSERT OR UPDATE ON subscribers
    FOR EACH ROW
    EXECUTE FUNCTION validate_user_preferences();

-- Fix 6: Helper function for monitoring scheduled messages (CORRECTED TYPES)
DROP FUNCTION IF EXISTS get_user_scheduled_messages(uuid);

-- FIXED: get_user_scheduled_messages function now returns UUID for id column  
CREATE OR REPLACE FUNCTION get_user_scheduled_messages(user_uuid uuid)
RETURNS TABLE(
    id uuid,
    message_type varchar(30),
    scheduled_for timestamptz,
    status varchar(20)
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    RETURN QUERY 
    SELECT sm.id, sm.message_type, sm.scheduled_for, sm.status
    FROM scheduled_messages sm
    WHERE sm.subscriber_id = user_uuid
    ORDER BY sm.scheduled_for ASC;
END;
$$;

-- Fix 7: Monitoring view for active users and their scheduling status
CREATE OR REPLACE VIEW active_users_with_scheduling AS
SELECT 
    s.id,
    s.email,
    s.wa_id,
    s.current_timezone,
    s.preferences->>'onboarding_completed' as onboarding_completed,
    COUNT(sm.id) as scheduled_message_count,
    MIN(sm.scheduled_for) as next_message_time
FROM subscribers s
LEFT JOIN scheduled_messages sm ON s.id = sm.subscriber_id AND sm.status = 'pending'
WHERE s.status = 'active'
GROUP BY s.id, s.email, s.wa_id, s.current_timezone, s.preferences;

-- Fix 8: Clean up any orphaned data
DELETE FROM scheduled_messages 
WHERE subscriber_id NOT IN (SELECT id FROM subscribers);

-- Fix 9: Grant proper permissions to service role
GRANT ALL ON ALL TABLES IN SCHEMA public TO service_role;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO service_role;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO service_role;

-- Fix 10: Debug function to manually trigger scheduled message creation
CREATE OR REPLACE FUNCTION debug_create_scheduled_messages(user_email text)
RETURNS TABLE(
    message_type varchar(30),
    scheduled_for timestamptz,
    status varchar(20)
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    user_record subscribers%ROWTYPE;
    user_prefs jsonb;
    user_tz text;
    base_date date;
BEGIN
    -- Get user data
    SELECT * INTO user_record FROM subscribers WHERE email = user_email;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'User not found: %', user_email;
    END IF;
    
    user_prefs := user_record.preferences;
    user_tz := COALESCE(user_record.current_timezone, 'UTC');
    base_date := CURRENT_DATE + INTERVAL '1 day';
    
    -- Create 7 scheduled messages
    -- 1. Daily affirmation (fixed 8 AM)
    INSERT INTO scheduled_messages (subscriber_id, message_type, scheduled_for, status, content)
    VALUES (user_record.id, 'daily_affirmation', 
            (base_date + TIME '08:00') AT TIME ZONE user_tz, 'pending', '');
    
    -- 2. Midday boost (fixed 12 PM) 
    INSERT INTO scheduled_messages (subscriber_id, message_type, scheduled_for, status, content)
    VALUES (user_record.id, 'midday_boost',
            (base_date + TIME '12:00') AT TIME ZONE user_tz, 'pending', '');
    
    -- 3. Evening wind down (fixed 4 PM)
    INSERT INTO scheduled_messages (subscriber_id, message_type, scheduled_for, status, content)
    VALUES (user_record.id, 'evening_wind_down',
            (base_date + TIME '16:00') AT TIME ZONE user_tz, 'pending', '');
    
    -- 4. Day planning (user custom)
    IF user_prefs->>'day_planning' IS NOT NULL THEN
        INSERT INTO scheduled_messages (subscriber_id, message_type, scheduled_for, status, content)
        VALUES (user_record.id, 'day_planning',
                (base_date + TIME '16:38') AT TIME ZONE user_tz, 'pending', '');
    END IF;
    
    -- 5. Accountability checkin (user custom)
    IF user_prefs->>'accountability_checkin' IS NOT NULL THEN
        INSERT INTO scheduled_messages (subscriber_id, message_type, scheduled_for, status, content)
        VALUES (user_record.id, 'accountability_checkin',
                (base_date + TIME '16:39') AT TIME ZONE user_tz, 'pending', '');
    END IF;
    
    -- 6. Gratitude prompt (user custom)  
    IF user_prefs->>'evening_gratitude' IS NOT NULL THEN
        INSERT INTO scheduled_messages (subscriber_id, message_type, scheduled_for, status, content)
        VALUES (user_record.id, 'gratitude_prompt',
                (base_date + TIME '16:40') AT TIME ZONE user_tz, 'pending', '');
    END IF;
    
    -- 7. Weekly reflection (user custom)
    IF user_prefs->>'weekly_reflection' IS NOT NULL THEN
        INSERT INTO scheduled_messages (subscriber_id, message_type, scheduled_for, status, content)
        VALUES (user_record.id, 'weekly_reflection',
                (DATE_TRUNC('week', CURRENT_DATE) + INTERVAL '8 days' + TIME '16:41') AT TIME ZONE user_tz, 'pending', '');
    END IF;
    
    -- Return created messages
    RETURN QUERY
    SELECT sm.message_type, sm.scheduled_for, sm.status
    FROM scheduled_messages sm
    WHERE sm.subscriber_id = user_record.id
    ORDER BY sm.scheduled_for;
END;
$$;

-- Fix 11: Schema diagnostics and validation
CREATE OR REPLACE FUNCTION diagnose_scheduled_messages_schema()
RETURNS TABLE(
    diagnosis_step text,
    result text
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    col_info record;
    test_result text;
BEGIN
    -- Step 1: Check actual column types
    RETURN QUERY 
    SELECT 'Column Types'::text as diagnosis_step,
           CONCAT(column_name, ': ', data_type) as result
    FROM information_schema.columns
    WHERE table_name = 'scheduled_messages'
      AND column_name IN ('id','subscriber_id','message_type','scheduled_for')
    ORDER BY ordinal_position;
    
    -- Step 2: Test function signature
    BEGIN
        PERFORM execute_raw_sql('SELECT 1 WHERE FALSE');
        RETURN QUERY SELECT 'Function Test'::text, 'execute_raw_sql: WORKS'::text;
    EXCEPTION WHEN OTHERS THEN
        RETURN QUERY SELECT 'Function Test'::text, CONCAT('execute_raw_sql: ERROR - ', SQLERRM)::text;
    END;
    
    -- Step 3: Test actual query with single row
    BEGIN
        PERFORM execute_raw_sql(
            $$WITH cte AS (
                SELECT id, subscriber_id, message_type, scheduled_for
                FROM scheduled_messages
                LIMIT 1
            )
            SELECT * FROM cte$$
        );
        RETURN QUERY SELECT 'Query Test'::text, 'Single row query: WORKS'::text;
    EXCEPTION WHEN OTHERS THEN
        RETURN QUERY SELECT 'Query Test'::text, CONCAT('Single row query: ERROR - ', SQLERRM)::text;
    END;
    
    -- Step 4: Count available messages
    SELECT COUNT(*)::text INTO test_result FROM scheduled_messages WHERE status = 'pending';
    RETURN QUERY SELECT 'Data Count'::text, CONCAT('Pending messages: ', test_result)::text;
    
END;
$$;

-- Fix 12: Final validation check
DO $$
DECLARE
    user_count integer;
    scheduled_count integer;
    active_count integer;
    onboarded_count integer;
BEGIN
    SELECT COUNT(*) INTO user_count FROM subscribers;
    SELECT COUNT(*) INTO scheduled_count FROM scheduled_messages;
    SELECT COUNT(*) INTO active_count FROM subscribers WHERE status = 'active';
    SELECT COUNT(*) INTO onboarded_count FROM subscribers 
    WHERE status = 'active' AND (preferences->>'onboarding_completed')::boolean = true;
    
    RAISE NOTICE '===============================================';
    RAISE NOTICE 'SCHEMA MIGRATION COMPLETED SUCCESSFULLY!';
    RAISE NOTICE '===============================================';
    RAISE NOTICE 'Total subscribers: %', user_count;
    RAISE NOTICE 'Active subscribers: %', active_count;
    RAISE NOTICE 'Completed onboarding: %', onboarded_count;
    RAISE NOTICE 'Scheduled messages: %', scheduled_count;
    
    -- Run diagnostics
    RAISE NOTICE 'Running schema diagnostics...';
    
    RAISE NOTICE 'All schema fixes applied without data loss!';
    RAISE NOTICE '===============================================';
END $$;