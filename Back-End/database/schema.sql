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

-- Scheduled Messages table (for background tasks)
CREATE TABLE IF NOT EXISTS scheduled_messages (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    subscriber_id UUID REFERENCES subscribers(id) ON DELETE CASCADE,
    
    -- Message Details
    message_type VARCHAR(30) NOT NULL 
        CHECK (message_type IN ('daily_affirmation', 'gratitude_prompt', 'weekly_reflection', 'check_in')),
    content TEXT NOT NULL,
    scheduled_for TIMESTAMP WITH TIME ZONE NOT NULL,
    
    -- Status
    status VARCHAR(20) DEFAULT 'pending' 
        CHECK (status IN ('pending', 'sent', 'failed', 'cancelled')),
    sent_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
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