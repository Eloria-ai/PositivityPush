-- Positivity Push Database Schema for Supabase
-- Run these commands in your Supabase SQL editor

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Subscribers table (main user data)
CREATE TABLE subscribers (
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
    timezone VARCHAR(50) DEFAULT 'UTC',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    activated_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    cancelled_at TIMESTAMP WITH TIME ZONE,
    last_payment_at TIMESTAMP WITH TIME ZONE,
    failed_payment_at TIMESTAMP WITH TIME ZONE
);

-- Conversations table (message history)
CREATE TABLE conversations (
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
CREATE TABLE user_progress (
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
CREATE TABLE scheduled_messages (
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
CREATE INDEX idx_subscribers_wa_id ON subscribers(wa_id);
CREATE INDEX idx_subscribers_stripe_session ON subscribers(stripe_session_id);
CREATE INDEX idx_subscribers_status ON subscribers(status);
CREATE INDEX idx_conversations_subscriber_timestamp ON conversations(subscriber_id, timestamp DESC);
CREATE INDEX idx_user_progress_subscriber_week ON user_progress(subscriber_id, week_start DESC);
CREATE INDEX idx_scheduled_messages_pending ON scheduled_messages(status, scheduled_for) WHERE status = 'pending';

-- Updated timestamp triggers
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_subscribers_updated_at 
    BEFORE UPDATE ON subscribers 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- RLS (Row Level Security) Policies
ALTER TABLE subscribers ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_progress ENABLE ROW LEVEL SECURITY;
ALTER TABLE scheduled_messages ENABLE ROW LEVEL SECURITY;

-- Service role can access everything (for backend)
CREATE POLICY "Service role can manage all data" ON subscribers
    FOR ALL USING (auth.role() = 'service_role');
    
CREATE POLICY "Service role can manage all conversations" ON conversations
    FOR ALL USING (auth.role() = 'service_role');
    
CREATE POLICY "Service role can manage all progress" ON user_progress
    FOR ALL USING (auth.role() = 'service_role');
    
CREATE POLICY "Service role can manage all scheduled messages" ON scheduled_messages
    FOR ALL USING (auth.role() = 'service_role');

-- Grant permissions to service role
GRANT ALL ON ALL TABLES IN SCHEMA public TO service_role;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO service_role;