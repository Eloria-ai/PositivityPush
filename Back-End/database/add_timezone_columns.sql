-- Migration: Add timezone tracking columns to subscribers table
-- This allows tracking of user's current timezone for traveling users

-- Add current_timezone column (user's actual timezone based on phone/IP)
ALTER TABLE subscribers 
ADD COLUMN IF NOT EXISTS current_timezone VARCHAR(50) DEFAULT 'UTC';

-- Add timezone_updated_at column (when timezone was last updated)
ALTER TABLE subscribers 
ADD COLUMN IF NOT EXISTS timezone_updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();

-- Add client_ip column (for IP-based timezone detection fallback)
ALTER TABLE subscribers 
ADD COLUMN IF NOT EXISTS client_ip VARCHAR(45); -- IPv6 max length

-- Add index for timezone queries
CREATE INDEX IF NOT EXISTS idx_subscribers_current_timezone ON subscribers(current_timezone);
CREATE INDEX IF NOT EXISTS idx_subscribers_timezone_updated ON subscribers(timezone_updated_at);

-- Update existing records to set current_timezone from original timezone column
UPDATE subscribers 
SET current_timezone = COALESCE(timezone, 'UTC')
WHERE current_timezone IS NULL OR current_timezone = 'UTC';

-- Comments for documentation
COMMENT ON COLUMN subscribers.current_timezone IS 'User''s current timezone based on phone/IP detection, updated when traveling';
COMMENT ON COLUMN subscribers.timezone_updated_at IS 'Timestamp when timezone was last updated';
COMMENT ON COLUMN subscribers.client_ip IS 'User''s IP address for timezone detection fallback';
COMMENT ON COLUMN subscribers.timezone IS 'Original timezone from onboarding (kept for reference)';