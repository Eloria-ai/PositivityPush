"""
Supabase Database Service for Positivity Push
Handles all database operations for subscriptions, conversations, and user data.
"""

from typing import Dict, Any, List, Optional
from supabase import Client
import logging

logger = logging.getLogger(__name__)

class SupabaseService:
    """Service class for Supabase database operations"""
    
    def __init__(self, client: Client):
        self.client = client
    
    # Subscription Management
    async def create_subscription(self, subscription_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new subscription record"""
        try:
            result = self.client.table("subscribers").insert(subscription_data).execute()
            logger.info(f"Created subscription: {result.data[0]['id']}")
            return result.data[0]
        except Exception as e:
            logger.error(f"Error creating subscription: {e}")
            raise
    
    async def get_subscription_by_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get subscription by Stripe session ID"""
        try:
            result = self.client.table("subscribers").select("*").eq("stripe_session_id", session_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error getting subscription by session: {e}")
            return None
    
    async def get_subscription_by_wa_id(self, wa_id: str) -> Optional[Dict[str, Any]]:
        """Get subscription by WhatsApp ID"""
        try:
            result = self.client.table("subscribers").select("*").eq("wa_id", wa_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error getting subscription by WhatsApp ID: {e}")
            return None
    
    async def get_subscription_by_id(self, subscription_id: str) -> Optional[Dict[str, Any]]:
        """Get subscription by ID"""
        try:
            result = self.client.table("subscribers").select("*").eq("id", subscription_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error getting subscription by id {subscription_id}: {e}")
            return None
    
    async def update_subscription(self, subscription_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update subscription record"""
        try:
            result = self.client.table("subscribers").update(updates).eq("id", subscription_id).execute()
            logger.info(f"Updated subscription: {subscription_id}")
            return result.data[0] if result.data else {}
        except Exception as e:
            logger.error(f"Error updating subscription: {e}")
            raise
    
    async def update_subscription_by_customer(self, customer_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update subscription by Stripe customer ID"""
        try:
            result = self.client.table("subscribers").update(updates).eq("stripe_customer_id", customer_id).execute()
            return result.data[0] if result.data else {}
        except Exception as e:
            logger.error(f"Error updating subscription by customer: {e}")
            raise
    
    async def update_subscription_by_stripe_id(self, stripe_subscription_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update subscription by Stripe subscription ID"""
        try:
            result = self.client.table("subscribers").update(updates).eq("stripe_subscription_id", stripe_subscription_id).execute()
            return result.data[0] if result.data else {}
        except Exception as e:
            logger.error(f"Error updating subscription by Stripe ID: {e}")
            raise
    
    # User Preferences Management
    async def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get user's scheduling preferences"""
        try:
            result = self.client.table("subscribers").select("preferences").eq("id", user_id).execute()
            if result.data:
                return result.data[0].get("preferences", {})
            return {}
        except Exception as e:
            logger.error(f"Error getting user preferences: {e}")
            return {}
    
    async def update_user_preferences(self, user_id: str, preferences: Dict[str, Any]) -> bool:
        """Update user's scheduling preferences"""
        try:
            result = self.client.table("subscribers").update({"preferences": preferences}).eq("id", user_id).execute()
            logger.info(f"Updated preferences for user: {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error updating user preferences: {e}")
            return False
    
    async def set_preference_value(self, user_id: str, key: str, value: Any) -> bool:
        """Set a specific preference value for a user"""
        try:
            # First get current preferences
            current_prefs = await self.get_user_preferences(user_id)
            
            # Update the specific key
            current_prefs[key] = value
            
            # Save back to database
            return await self.update_user_preferences(user_id, current_prefs)
        except Exception as e:
            logger.error(f"Error setting preference {key} for user {user_id}: {e}")
            return False
    
    async def is_onboarding_completed(self, user_id: str) -> bool:
        """Check if user has completed onboarding"""
        try:
            preferences = await self.get_user_preferences(user_id)
            return preferences.get("onboarding_completed", False)
        except Exception as e:
            logger.error(f"Error checking onboarding status: {e}")
            return False
    
    async def mark_onboarding_completed(self, user_id: str) -> bool:
        """Mark user's onboarding as completed"""
        return await self.set_preference_value(user_id, "onboarding_completed", True)
    
    async def get_users_needing_onboarding(self) -> List[Dict[str, Any]]:
        """Get users who haven't completed onboarding yet"""
        try:
            result = (
                self.client.table("subscribers")
                .select("*")
                .eq("status", "active")
                .filter("preferences->>onboarding_completed", "eq", "false")
                .execute()
            )
            return result.data
        except Exception as e:
            logger.error(f"Error getting users needing onboarding: {e}")
            return []
    
    # Conversation Management
    async def log_conversation(
        self, 
        subscriber_id: str, 
        content: str, 
        message_type: str, 
        wa_message_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Log conversation message"""
        try:
            conversation_data = {
                "subscriber_id": subscriber_id,
                "content": content,
                "message_type": message_type,  # 'user' or 'assistant'
                "wa_message_id": wa_message_id,
                "timestamp": "now()"
            }
            
            result = self.client.table("conversations").insert(conversation_data).execute()
            return result.data[0] if result.data else {}
        except Exception as e:
            logger.error(f"Error logging conversation: {e}")
            raise
    
    async def get_conversation_history(
        self, 
        subscriber_id: str, 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get recent conversation history for user"""
        try:
            result = (
                self.client.table("conversations")
                .select("*")
                .eq("subscriber_id", subscriber_id)
                .order("timestamp", desc=True)
                .limit(limit)
                .execute()
            )
            return result.data[::-1]  # Reverse to get chronological order
        except Exception as e:
            logger.error(f"Error getting conversation history: {e}")
            return []
    
    # User Progress Tracking
    async def update_user_goals(self, subscriber_id: str, goals: Dict[str, Any]) -> Dict[str, Any]:
        """Update user's personal goals and preferences"""
        try:
            result = self.client.table("subscribers").update({
                "personal_goals": goals,
                "updated_at": "now()"
            }).eq("id", subscriber_id).execute()
            return result.data[0] if result.data else {}
        except Exception as e:
            logger.error(f"Error updating user goals: {e}")
            raise
    
    async def log_user_progress(
        self, 
        subscriber_id: str, 
        progress_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Log weekly user progress"""
        try:
            progress_record = {
                "subscriber_id": subscriber_id,
                "week_start": progress_data.get("week_start"),
                "wins": progress_data.get("wins", []),
                "challenges": progress_data.get("challenges", []),
                "goal_progress": progress_data.get("goal_progress", {}),
                "mood_patterns": progress_data.get("mood_patterns", []),
                "created_at": "now()"
            }
            
            result = self.client.table("user_progress").insert(progress_record).execute()
            return result.data[0] if result.data else {}
        except Exception as e:
            logger.error(f"Error logging user progress: {e}")
            raise
    
    # Active Subscribers for Background Tasks
    async def get_active_subscribers(self) -> List[Dict[str, Any]]:
        """Get all active subscribers for daily/weekly messaging"""
        try:
            result = (
                self.client.table("subscribers")
                .select("*")
                .eq("status", "active")
                .execute()
            )
            return result.data
        except Exception as e:
            logger.error(f"Error getting active subscribers: {e}")
            return []
    
    async def get_subscribers_for_daily_message(self, timezone: str = None) -> List[Dict[str, Any]]:
        """Get subscribers ready for daily messages based on current timezone"""
        try:
            query = self.client.table("subscribers").select("*").eq("status", "active")
            
            if timezone:
                # Use current_timezone instead of old timezone field
                query = query.eq("current_timezone", timezone)
            
            result = query.execute()
            return result.data
        except Exception as e:
            logger.error(f"Error getting subscribers for daily message: {e}")
            return []
    
    async def get_subscribers_for_scheduled_message(self, message_type: str, current_time: str, timezone: str = None) -> List[Dict[str, Any]]:
        """Get subscribers who should receive a specific message type at current time"""
        try:
            # Base query for active subscribers with completed onboarding
            query = (
                self.client.table("subscribers")
                .select("*")
                .eq("status", "active")
                .filter("preferences->>onboarding_completed", "eq", "true")
            )
            
            if timezone:
                # Use current_timezone instead of preferences timezone
                query = query.eq("current_timezone", timezone)
            
            # Get all matching subscribers
            result = query.execute()
            subscribers = result.data
            
            # Filter by specific message time
            filtered_subscribers = []
            for subscriber in subscribers:
                preferences = subscriber.get("preferences", {})
                
                if message_type == "weekly_reflection":
                    # Special handling for weekly reflection (day + time)
                    weekly_pref = preferences.get("weekly_reflection", {})
                    if isinstance(weekly_pref, dict):
                        scheduled_time = weekly_pref.get("time")
                    else:
                        scheduled_time = None
                else:
                    # Regular daily messages
                    scheduled_time = preferences.get(message_type)
                
                # Check if current time matches scheduled time (with 5 minute window)
                if scheduled_time and self._is_time_match(current_time, scheduled_time):
                    filtered_subscribers.append(subscriber)
            
            return filtered_subscribers
            
        except Exception as e:
            logger.error(f"Error getting subscribers for {message_type}: {e}")
            return []
    
    def _is_time_match(self, current_time: str, scheduled_time: str, window_minutes: int = 5) -> bool:
        """Check if current time matches scheduled time within a window"""
        try:
            from datetime import datetime, timedelta
            
            # Parse times
            current = datetime.strptime(current_time, "%H:%M")
            scheduled = datetime.strptime(scheduled_time, "%H:%M")
            
            # Create time window
            window = timedelta(minutes=window_minutes)
            start_window = scheduled - window
            end_window = scheduled + window
            
            # Handle day boundary crossings
            if start_window.day != scheduled.day:
                # Window crosses midnight backward
                return current >= start_window or current <= end_window
            elif end_window.day != scheduled.day:
                # Window crosses midnight forward  
                return current >= start_window or current <= end_window
            else:
                # Normal case
                return start_window <= current <= end_window
                
        except Exception as e:
            logger.error(f"Error checking time match: {e}")
            return False
    
    # ===== SCHEDULED MESSAGES METHODS (New Architecture) =====
    
    async def get_due_scheduled_messages(self, batch_size: int = 500, use_skip_locked: bool = True) -> List[Dict[str, Any]]:
        """
        Get due messages using SKIP LOCKED to prevent race conditions.
        Updates status to 'queued' atomically to prevent duplicate processing.
        """
        try:
            if use_skip_locked:
                # Use raw SQL with SKIP LOCKED for atomic queue+lock operation
                sql = f"""
                    WITH cte AS (
                        SELECT id, subscriber_id, message_type, scheduled_for
                        FROM   scheduled_messages
                        WHERE  status = 'pending'
                        AND    scheduled_for <= now()
                        ORDER  BY scheduled_for
                        LIMIT  {batch_size}
                        FOR UPDATE SKIP LOCKED
                    )
                    UPDATE scheduled_messages
                    SET    status = 'queued',
                           updated_at = now()
                    FROM   cte
                    WHERE  scheduled_messages.id = cte.id
                    RETURNING scheduled_messages.id, scheduled_messages.subscriber_id, 
                              scheduled_messages.message_type, scheduled_messages.scheduled_for;
                """
                
                # IMPORTANT: This requires the following RPC function in Supabase SQL Editor:
                # CREATE OR REPLACE FUNCTION execute_raw_sql(query text)
                # RETURNS TABLE(id bigint, subscriber_id uuid, message_type text, scheduled_for timestamptz)
                # LANGUAGE plpgsql SECURITY DEFINER
                # AS $$
                # BEGIN
                #     RETURN QUERY EXECUTE query;
                # END;
                # $$;
                
                result = self.client.rpc("execute_raw_sql", {"query": sql}).execute()
                return result.data if result.data else []
            else:
                # Fallback without SKIP LOCKED (for testing)
                from datetime import datetime
                current_time = datetime.utcnow().isoformat()
                result = self.client.table("scheduled_messages") \
                    .select("id, subscriber_id, message_type, scheduled_for") \
                    .eq("status", "pending") \
                    .lte("scheduled_for", current_time) \
                    .order("scheduled_for") \
                    .limit(batch_size) \
                    .execute()
                return result.data if result.data else []
                
        except Exception as e:
            logger.error(f"Error getting due scheduled messages: {e}")
            return []
    
    async def get_message_with_user_context(self, message_id: int) -> Optional[Dict[str, Any]]:
        """Get message details with full subscriber context for AI generation"""
        try:
            # Join scheduled_messages with subscribers to get full context
            result = self.client.table("scheduled_messages") \
                .select("""
                    id, message_type, scheduled_for, status,
                    subscriber:subscribers (
                        id, email, wa_id, phone_number, plan_type,
                        personal_goals, communication_style, active_challenges,
                        current_timezone, preferences
                    )
                """) \
                .eq("id", message_id) \
                .execute()
            
            if result.data and len(result.data) > 0:
                message_row = result.data[0]
                return {
                    'id': message_row['id'],
                    'message_type': message_row['message_type'], 
                    'scheduled_for': message_row['scheduled_for'],
                    'status': message_row['status'],
                    'subscriber': message_row['subscriber']
                }
            return None
            
        except Exception as e:
            logger.error(f"Error getting message with user context: {e}")
            return None
    
    async def mark_message_sent(self, message_id: int) -> bool:
        """Mark message as successfully sent"""
        try:
            from datetime import datetime
            result = self.client.table("scheduled_messages") \
                .update({
                    "status": "sent",
                    "updated_at": datetime.utcnow().isoformat()
                }) \
                .eq("id", message_id) \
                .execute()
            
            logger.info(f"Marked message {message_id} as sent")
            return True
            
        except Exception as e:
            logger.error(f"Error marking message sent: {e}")
            return False
    
    async def mark_message_failed(self, message_id: int, error: str) -> bool:
        """Mark message as failed with error details (prevents infinite requeues)"""
        try:
            from datetime import datetime
            result = self.client.table("scheduled_messages") \
                .update({
                    "status": "failed",
                    "last_error": error[:500],  # Truncate error to keep row size manageable
                    "updated_at": datetime.utcnow().isoformat()
                }) \
                .eq("id", message_id) \
                .execute()
            
            logger.warning(f"Marked message {message_id} as failed: {error[:100]}")
            return True
            
        except Exception as e:
            logger.error(f"Error marking message failed: {e}")
            return False
    
    async def cleanup_old_messages(self, days_old: int = 7) -> int:
        """Clean up old completed/failed messages to prevent table bloat"""
        try:
            from datetime import datetime, timedelta
            cutoff_date = (datetime.utcnow() - timedelta(days=days_old)).isoformat()
            
            result = self.client.table("scheduled_messages") \
                .delete() \
                .in_("status", ["sent", "failed"]) \
                .lt("updated_at", cutoff_date) \
                .execute()
            
            cleaned_count = len(result.data) if result.data else 0
            logger.info(f"Cleaned up {cleaned_count} old scheduled messages")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Error cleaning up old messages: {e}")
            return 0
    
    async def populate_scheduled_messages_from_preferences(self) -> int:
        """Migration utility: populate scheduled_messages from user preferences"""
        try:
            # Get all active subscribers with preferences
            result = self.client.table("subscribers") \
                .select("id, current_timezone, preferences") \
                .eq("status", "active") \
                .execute()
            
            migrated_count = 0
            # Implementation would create scheduled_messages entries based on user preferences
            # This is a placeholder for the actual migration logic
            
            logger.info(f"Migrated {migrated_count} users to scheduled_messages")
            return migrated_count
            
        except Exception as e:
            logger.error(f"Error populating scheduled messages: {e}")
            return 0
