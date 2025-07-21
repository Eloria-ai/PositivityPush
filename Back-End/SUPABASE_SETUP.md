# Supabase Setup Guide for Positivity Push

## 1. Run Database Schema

Copy and paste the entire contents of `database/schema.sql` into your Supabase SQL Editor and run it.

This will:
- Create all required tables with correct schema
- Add the critical `execute_raw_sql()` function for SKIP LOCKED operations  
- Set up proper indexes for production performance
- Configure Row Level Security (RLS) policies
- Add triggers for updated_at columns

## 2. Verify Critical Components

After running the schema, verify these key items exist:

### Tables
- `subscribers` - User data with proper timezone columns
- `conversations` - Message history  
- `user_progress` - Weekly tracking
- `scheduled_messages` - **New architecture queue table**

### Functions
- `execute_raw_sql(query text)` - **Critical for SKIP LOCKED operations**
- `update_updated_at_column()` - Timestamp triggers

### Indexes
- `idx_scheduled_messages_pending` - **Critical for driver performance**
- `idx_subscribers_current_timezone` - Timezone-based queries
- `idx_subscribers_onboarding` - Onboarding status filter

## 3. Test the Setup

You can test the complete flow with these SQL commands:

```sql
-- Insert a test user
INSERT INTO subscribers (email, phone_number, status, current_timezone, preferences) 
VALUES (
  'test@example.com', 
  '+15551234567', 
  'active', 
  'America/New_York',
  '{"onboarding_completed": true, "day_planning": "09:00", "accountability_checkin": "19:00"}'
);

-- Insert a test scheduled message
INSERT INTO scheduled_messages (subscriber_id, message_type, scheduled_for, status)
SELECT id, 'daily_affirmation', now() - interval '5 minutes', 'pending'
FROM subscribers 
WHERE email = 'test@example.com';

-- Test the SKIP LOCKED operation
SELECT execute_raw_sql('
  WITH cte AS (
    SELECT id, subscriber_id, message_type, scheduled_for
    FROM   scheduled_messages
    WHERE  status = ''pending''
    AND    scheduled_for <= now()
    ORDER  BY scheduled_for
    LIMIT  10
    FOR UPDATE SKIP LOCKED
  )
  UPDATE scheduled_messages
  SET    status = ''queued'',
         updated_at = now()
  FROM   cte
  WHERE  scheduled_messages.id = cte.id
  RETURNING scheduled_messages.id, scheduled_messages.subscriber_id, 
            scheduled_messages.message_type, scheduled_messages.scheduled_for;
');
```

If this query returns your test message, the setup is working correctly.

## 4. Environment Variables

Make sure your backend has these environment variables:

```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key
```

Use the **service role key**, not the anon key, since the backend needs full database access.

## 5. Common Issues

**Issue: `execute_raw_sql` function not found**
- Solution: Make sure you ran the complete schema.sql file
- The function must be created with SECURITY DEFINER permissions

**Issue: SKIP LOCKED not working**  
- Solution: Ensure you're using PostgreSQL 9.5+ (Supabase uses 15.x)
- Verify the function has proper permissions

**Issue: RLS blocking operations**
- Solution: Use the service role key, which bypasses RLS
- Or check that RLS policies allow service_role access

## 6. Next Steps

Once Supabase is set up:
1. Test the Celery worker with `process_personalized_messages` task
2. Verify the driver+dispatcher pattern works end-to-end  
3. Check that messages transition: pending → queued → sent/failed
4. Monitor the scheduled_messages table for proper state management

The new architecture is now ready for production deployment.