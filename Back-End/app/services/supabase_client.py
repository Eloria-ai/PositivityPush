"""
Supabase Database Service for Positivity Push
Handles all database operations for subscriptions, conversations, and user data.
"""

from typing import Dict, Any, List, Optional
from supabase import Client
import logging
from datetime import datetime, timedelta
import pytz

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
        """Get user's scheduling preferences including timezone from subscription"""
        try:
            result = self.client.table("subscribers").select(
                "preferences, current_timezone"
            ).eq("id", user_id).execute()
            if result.data:
                data = result.data[0]
                preferences = data.get("preferences", {})
                
                # Include timezone in preferences for completion checking
                if data.get("current_timezone"):
                    preferences["current_timezone"] = data["current_timezone"]
                
                # Ensure onboarding status defaults are set if not in preferences
                if "onboarding_completed" not in preferences:
                    preferences["onboarding_completed"] = True
                if "onboarding_step" not in preferences:
                    preferences["onboarding_step"] = None
                
                return preferences
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
    
    async def batch_update_preferences(self, user_id: str, preference_updates: Dict[str, Any]) -> bool:
        """Batch update multiple preference values in a single database call"""
        try:
            # Get current preferences
            current_prefs = await self.get_user_preferences(user_id)
            
            # Merge updates
            updated_prefs = {**current_prefs, **preference_updates}
            
            # Single database update
            result = self.client.table("subscribers").update({"preferences": updated_prefs}).eq("id", user_id).execute()
            logger.info(f"Batch updated preferences for user: {user_id}, keys: {list(preference_updates.keys())}")
            
            # If any scheduling preferences were updated and user is onboarded, recreate scheduled messages
            scheduling_preferences = ['day_planning', 'accountability_checkin', 'evening_gratitude', 'weekly_reflection', 'current_timezone']
            updated_scheduling = any(key in scheduling_preferences for key in preference_updates.keys())
            if updated_scheduling and updated_prefs.get('onboarding_completed'):
                logger.info(f"🔄 Scheduling preferences updated for user {user_id}, recreating scheduled messages")
                await self.create_scheduled_messages_for_user(user_id)
            
            return True
        except Exception as e:
            logger.error(f"Error batch updating preferences: {e}")
            return False
    
    async def set_preference_value(self, user_id: str, key: str, value: Any) -> bool:
        """Set a specific preference value for a user"""
        try:
            # First get current preferences
            current_prefs = await self.get_user_preferences(user_id)
            
            # Update the specific key
            current_prefs[key] = value
            
            # Save back to database
            success = await self.update_user_preferences(user_id, current_prefs)
            
            # If this is a scheduling preference and user is fully onboarded, recreate scheduled messages
            scheduling_preferences = ['day_planning', 'accountability_checkin', 'evening_gratitude', 'weekly_reflection', 'current_timezone']
            if success and key in scheduling_preferences and current_prefs.get('onboarding_completed'):
                logger.info(f"🔄 Scheduling preference '{key}' updated for user {user_id}, recreating scheduled messages")
                await self.create_scheduled_messages_for_user(user_id)
            
            return success
        except Exception as e:
            logger.error(f"Error setting preference {key} for user {user_id}: {e}")
            return False
    
    # Daily Plans Management (for context-aware messaging)
    async def set_pending_intent(self, user_id: str, intent: str, date: str = None) -> bool:
        """Set pending intent for capturing user responses (e.g., after day planning prompt)"""
        try:
            pending_intent = {"intent": intent, "date": date, "timestamp": datetime.utcnow().isoformat()}
            return await self.set_preference_value(user_id, "pending_intent", pending_intent)
        except Exception as e:
            logger.error(f"Error setting pending intent for user {user_id}: {e}")
            return False
    
    async def clear_pending_intent(self, user_id: str) -> bool:
        """Clear pending intent after capturing user response"""
        try:
            return await self.set_preference_value(user_id, "pending_intent", None)
        except Exception as e:
            logger.error(f"Error clearing pending intent for user {user_id}: {e}")
            return False
    
    async def store_daily_plan(self, user_id: str, plan_date: str, items: List[str], raw_text: str) -> bool:
        """Store user's daily plan for context-aware check-ins"""
        try:
            # Use upsert to handle duplicates (replace if same date)
            result = self.client.table("daily_plans").upsert({
                "subscriber_id": user_id,
                "plan_date": plan_date,
                "items": items,
                "raw_text": raw_text
            }).execute()
            
            logger.info(f"Stored daily plan for user {user_id} on {plan_date}: {len(items)} items")
            return True
        except Exception as e:
            logger.error(f"Error storing daily plan for user {user_id}: {e}")
            return False
    
    async def get_daily_plan_for_date(self, user_id: str, date: str) -> Optional[Dict[str, Any]]:
        """Get user's daily plan for specific date"""
        try:
            result = self.client.table("daily_plans") \
                .select("*") \
                .eq("subscriber_id", user_id) \
                .eq("plan_date", date) \
                .execute()
            
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error getting daily plan for user {user_id} on {date}: {e}")
            return None
    
    async def get_weekly_goals(self, user_id: str, week_start: str) -> Optional[Dict[str, Any]]:
        """Get user's weekly goals for specific week"""
        try:
            result = self.client.table("weekly_goals") \
                .select("*") \
                .eq("subscriber_id", user_id) \
                .eq("week_start", week_start) \
                .execute()
            
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error getting weekly goals for user {user_id}, week {week_start}: {e}")
            return None
    
    def parse_daily_plan_items(self, user_text: str) -> List[str]:
        """Parse user's daily plan response into structured items"""
        if not user_text:
            return []
        
        items = []
        lines = user_text.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Handle different list formats
            # Bullet points: "- task", "* task", "• task"
            if line.startswith(('-', '*', '•')):
                item = line[1:].strip()
                if item:
                    items.append(item)
            # Numbered: "1. task", "1) task"  
            elif line[0].isdigit() and ('. ' in line or ') ' in line):
                # Find the separator and extract the task
                if '. ' in line:
                    item = line.split('. ', 1)[1].strip()
                elif ') ' in line:
                    item = line.split(') ', 1)[1].strip()
                if item:
                    items.append(item)
            # Comma-separated in single line
            elif ',' in user_text and len(lines) == 1:
                # Split by commas if single line
                comma_items = [item.strip() for item in user_text.split(',')]
                items.extend([item for item in comma_items if item])
                break  # Don't process more lines if we handled commas
            # Plain task (no formatting)
            else:
                items.append(line)
        
        # Clean up and dedupe
        cleaned_items = []
        for item in items:
            # Remove common prefixes and clean
            item = item.strip().strip('.,')
            if item and item not in cleaned_items:
                cleaned_items.append(item)
        
        # Cap to 10 items max
        return cleaned_items[:10]
    
    def parse_task_completion(self, user_text: str) -> List[int]:
        """Parse user's task completion response (e.g., '1,3', '1 and 3', 'just 2')"""
        import re
        if not user_text:
            return []
        
        # Find all numbers in the text
        numbers = re.findall(r'\b(\d+)\b', user_text.lower())
        completed_items = []
        
        for num_str in numbers:
            try:
                num = int(num_str)
                if 1 <= num <= 10:  # Valid task numbers (1-10)
                    completed_items.append(num)
            except ValueError:
                continue
        
        # Remove duplicates and sort
        return sorted(list(set(completed_items)))
    
    async def update_task_completion(self, user_id: str, plan_date: str, completed_items: List[int], raw_response: str) -> bool:
        """Update daily plan with task completion status"""
        try:
            # Get the current daily plan
            result = self.client.table("daily_plans") \
                .select("*") \
                .eq("subscriber_id", user_id) \
                .eq("plan_date", plan_date) \
                .execute()
            
            if not result.data:
                logger.warning(f"No daily plan found for user {user_id} on {plan_date}")
                return False
            
            daily_plan = result.data[0]
            current_items = daily_plan.get('items', [])
            
            # Create completion status for each item
            completion_status = []
            for i, item in enumerate(current_items):
                item_number = i + 1  # 1-indexed for user display
                is_completed = item_number in completed_items
                completion_status.append({
                    "item": item,
                    "completed": is_completed,
                    "item_number": item_number
                })
            
            # Update the daily plan with completion data
            update_result = self.client.table("daily_plans") \
                .update({
                    "completion_status": completion_status,
                    "completion_response": raw_response,
                    "completed_at": datetime.now().isoformat() if completed_items else None
                }) \
                .eq("id", daily_plan['id']) \
                .execute()
            
            logger.info(f"Updated task completion for user {user_id}: {completed_items}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating task completion for user {user_id}: {e}")
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
        """Mark user's onboarding as completed and create scheduled messages"""
        # CRITICAL: Always complete onboarding first - this MUST succeed
        # Force deployment verification
        success = await self.set_preference_value(user_id, "onboarding_completed", True)
        
        if success:
            # NEW: Create scheduled messages for the user (safe to fail)
            try:
                message_creation_success = await self.create_scheduled_messages_for_user(user_id)
                if message_creation_success:
                    logger.info(f"✅ Onboarding completed and scheduled messages created for user {user_id}")
                else:
                    logger.warning(f"⚠️ Onboarding completed but scheduled message creation failed for user {user_id}")
            except Exception as e:
                logger.error(f"⚠️ Onboarding completed but scheduled message creation errored for user {user_id}: {e}")
                # Don't return False - onboarding completion should never fail due to scheduling issues
        
        # Always return the original onboarding completion result
        return success
    
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
    async def get_recent_conversations(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent conversation messages for context"""
        try:
            result = (
                self.client.table("conversations")
                .select("content, message_type, timestamp")
                .eq("subscriber_id", user_id)
                .order("timestamp", desc=True)
                .limit(limit)
                .execute()
            )
            return result.data if result.data else []
        except Exception as e:
            logger.error(f"Error getting recent conversations: {e}")
            return []

    async def log_conversation(
        self, 
        subscriber_id: str, 
        content: str, 
        message_type: str, 
        wa_message_id: Optional[str] = None,
        context_used: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Log conversation message with optional metadata in context_used"""
        try:
            import json
            from datetime import datetime
            conversation_data = {
                "subscriber_id": subscriber_id,
                "content": content,
                "message_type": message_type,  # 'user', 'assistant', or 'pattern'
                "wa_message_id": wa_message_id,
                "context_used": json.dumps(context_used) if context_used else None,
                "timestamp": datetime.utcnow().isoformat() + "+00:00"
            }
            
            result = self.client.table("conversations").insert(conversation_data).execute()
            return result.data[0] if result.data else {}
        except Exception as e:
            logger.error(f"Error logging conversation: {e}")
            raise
    
    async def get_conversation_by_message_id(self, wa_message_id: str) -> Optional[Dict[str, Any]]:
        """Check if a message has already been processed by looking up the Twilio MessageSid"""
        try:
            result = (
                self.client.table("conversations")
                .select("id, subscriber_id, wa_message_id, timestamp")
                .eq("wa_message_id", wa_message_id)
                .limit(1)
                .execute()
            )
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error checking conversation by message ID: {e}")
            return None
    
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
                sql = f"""WITH cte AS (
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
                          scheduled_messages.message_type, scheduled_messages.scheduled_for;"""
                
                # IMPORTANT: This requires the following RPC function in Supabase SQL Editor:
                # CREATE OR REPLACE FUNCTION execute_raw_sql(query text)
                # RETURNS TABLE(id uuid, subscriber_id uuid, message_type varchar(30), scheduled_for timestamptz)
                # LANGUAGE plpgsql SECURITY DEFINER
                # AS $$
                # BEGIN
                #     RETURN QUERY EXECUTE query;
                # END;
                # $$;
                
                # Debug: Log the exact SQL query being sent
                logger.debug(f"🔍 SQL Query for execute_raw_sql: {repr(sql)}")
                logger.debug(f"🔍 SQL Query length: {len(sql)} chars")
                logger.debug(f"🔍 SQL Query first 100 chars: {sql[:100]}")
                
                result = self.client.rpc("execute_raw_sql", {"query": sql}).execute()
                logger.debug(f"🔍 RPC result data count: {len(result.data) if result.data else 0}")
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
    
    async def get_message_with_user_context(self, message_id: str) -> Optional[Dict[str, Any]]:
        """Get message details with full subscriber context for AI generation"""
        try:
            # Join scheduled_messages with subscribers to get full context
            result = self.client.table("scheduled_messages") \
                .select("""
                    id, message_type, scheduled_for, status, content, subscriber_id,
                    subscriber:subscribers!scheduled_messages_subscriber_id_fkey (
                        id, email, wa_id, phone_number, plan_type,
                        personal_goals, communication_style, active_challenges,
                        current_timezone, preferences
                    )
                """) \
                .eq("id", message_id) \
                .execute()
            
            if result.data and len(result.data) > 0:
                message_row = result.data[0]
                
                # Handle subscriber data safely (PostgREST can return under different keys)
                subscriber_data = message_row.get('subscriber') or message_row.get('subscribers')
                
                if not subscriber_data:
                    # Fallback: fetch subscriber directly using FK
                    subscriber_id = message_row.get('subscriber_id')
                    if subscriber_id:
                        logger.info("Fetching subscriber directly for message_id=%s subscriber_id=%s", message_id, subscriber_id)
                        subscriber_result = self.client.table("subscribers").select(
                            "id, email, wa_id, phone_number, plan_type, "
                            "personal_goals, communication_style, active_challenges, "
                            "current_timezone, preferences"
                        ).eq("id", subscriber_id).limit(1).execute()
                        subscriber_data = subscriber_result.data[0] if subscriber_result.data else None
                
                if not subscriber_data:
                    logger.warning("subscriber_context_missing message_id=%s", message_id)
                    return None
                
                return {
                    'id': message_row['id'],
                    'message_type': message_row['message_type'], 
                    'scheduled_for': message_row['scheduled_for'],
                    'status': message_row['status'],
                    'content': message_row.get('content'),  # Include pre-generated content
                    'subscriber': subscriber_data
                }
            return None
            
        except Exception as e:
            logger.error("Error getting message with user context: %s", str(e))
            return None
    
    async def get_scheduled_message_content(self, message_id: str) -> Optional[Dict[str, Any]]:
        """Get scheduled message with content field for pre-generated messages"""
        try:
            result = self.client.table("scheduled_messages") \
                .select("id, message_type, content, status") \
                .eq("id", message_id) \
                .execute()
            
            if result.data and len(result.data) > 0:
                return result.data[0]
            return None
            
        except Exception as e:
            logger.error(f"Error getting scheduled message content: {e}")
            return None
    
    async def mark_message_sent(self, message_id: str) -> bool:
        """Mark message as successfully sent and schedule next occurrence"""
        try:
            from datetime import datetime, timedelta
            
            # First, get the message details to schedule next occurrence
            message_result = self.client.table("scheduled_messages") \
                .select("id, subscriber_id, message_type, scheduled_for") \
                .eq("id", message_id) \
                .execute()
            
            if not message_result.data:
                logger.error(f"Message {message_id} not found for rescheduling")
                return False
                
            message = message_result.data[0]
            message_type = message["message_type"]
            subscriber_id = message["subscriber_id"]
            current_scheduled_for = datetime.fromisoformat(message["scheduled_for"].replace('Z', '+00:00'))
            
            # Mark current message as sent (with race condition protection)
            result = self.client.table("scheduled_messages") \
                .update({
                    "status": "sent",
                    "updated_at": datetime.utcnow().isoformat() + "+00:00"
                }) \
                .eq("id", message_id) \
                .eq("status", "queued") \
                .execute()
            
            if not result.data:
                logger.warning("skip_send_state_race message_id=%s", message_id)
                return False
            
            # Schedule next occurrence for recurring messages
            next_scheduled_time = None
            
            if message_type in ["daily_affirmation", "midday_boost", "evening_wind_down", 
                               "day_planning", "accountability_checkin", "gratitude_prompt"]:
                # Daily messages: schedule for next day at same time
                next_scheduled_time = current_scheduled_for + timedelta(days=1)
                
            elif message_type == "weekly_reflection":
                # Weekly messages: schedule for next week at same time
                next_scheduled_time = current_scheduled_for + timedelta(weeks=1)
            
            # Create next occurrence if this is a recurring message (with duplicate prevention)
            if next_scheduled_time:
                next_iso = next_scheduled_time.isoformat()
                
                if not self._exists_scheduled_message(subscriber_id, message_type, next_iso):
                    next_message_data = {
                        "subscriber_id": subscriber_id,
                        "message_type": message_type,
                        "scheduled_for": next_iso,
                        "status": "pending",
                        "content": ""  # Will be generated when dispatched
                    }
                    
                    next_result = self.client.table("scheduled_messages").insert(next_message_data).execute()
                    
                    if next_result.data:
                        next_message_id = next_result.data[0]["id"]
                        logger.info(f"Message {message_id} sent and next occurrence {next_message_id} scheduled for {next_scheduled_time}")
                    else:
                        logger.warning(f"Message {message_id} sent but failed to schedule next occurrence")
                else:
                    logger.info("skip_duplicate_next_occurrence message_id=%s type=%s when=%s", message_id, message_type, next_iso)
            else:
                logger.info(f"Non-recurring message {message_id} marked as sent")
            
            return True
            
        except Exception as e:
            logger.error(f"Error marking message sent and rescheduling: {e}")
            return False
    
    async def mark_message_failed(self, message_id: str, error: str) -> bool:
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
    
    async def schedule_onboarding_message(self, subscriber_id: str, message_type: str, content: str, delay_seconds: int = 0) -> Optional[str]:
        """Schedule an onboarding message for unified dispatcher delivery"""
        try:
            from datetime import datetime, timedelta
            
            scheduled_for = datetime.utcnow() + timedelta(seconds=delay_seconds)
            
            message_data = {
                "subscriber_id": subscriber_id,
                "message_type": message_type,
                "content": content,  # Pre-generated content for onboarding
                "scheduled_for": scheduled_for.isoformat() + "+00:00",
                "status": "pending"
            }
            
            result = self.client.table("scheduled_messages").insert(message_data).execute()
            
            if result.data:
                message_id = result.data[0]["id"]
                logger.info(f"Scheduled onboarding message: {message_id}, type: {message_type}")
                return message_id
            
            return None
            
        except Exception as e:
            logger.error(f"Error scheduling onboarding message: {e}")
            return None

    async def create_scheduled_messages_for_user(self, user_id: str) -> bool:
        """
        Create all scheduled messages for newly onboarded user
        Creates 7 message types: 3 fixed affirmations + 4 user-customized messages
        """
        try:
            logger.info(f"🔧 Starting scheduled message creation for user {user_id}")
            
            # FIRST: Clean up any existing pending scheduled messages for this user
            # This prevents duplicates when preferences are updated or onboarding is re-run
            try:
                cleanup_result = self.client.table("scheduled_messages") \
                    .delete() \
                    .eq("subscriber_id", user_id) \
                    .eq("status", "pending") \
                    .execute()
                
                cleanup_count = len(cleanup_result.data) if cleanup_result.data else 0
                if cleanup_count > 0:
                    logger.info(f"🧹 Cleaned up {cleanup_count} existing pending messages for user {user_id}")
                else:
                    logger.info(f"🧹 No existing pending messages to clean up for user {user_id}")
                    
            except Exception as cleanup_error:
                logger.error(f"⚠️ Error cleaning up pending messages for user {user_id}: {cleanup_error}")
                # Continue with creation even if cleanup fails
            
            # Get user data
            preferences = await self.get_user_preferences(user_id)
            logger.info(f"📋 User preferences for scheduled message creation (user {user_id}): {preferences}")
            
            # Log what preference keys are available for debugging
            available_keys = list(preferences.keys()) if preferences else []
            logger.info(f"🔍 Available preference keys: {available_keys}")
            
            # Get subscriber data for fixed affirmation times
            subscriber_result = self.client.table("subscribers") \
                .select("id, current_timezone, morning_positivity, midday_positivity, afternoon_positivity") \
                .eq("id", user_id) \
                .execute()
            
            if not subscriber_result.data:
                logger.error(f"❌ Subscriber not found for user {user_id}")
                return False
                
            subscriber = subscriber_result.data[0]
            user_timezone = subscriber.get("current_timezone") or preferences.get("current_timezone", "UTC")
            logger.info(f"📍 User timezone: {user_timezone}")
            
            # Validate timezone
            try:
                tz = pytz.timezone(user_timezone)
            except pytz.exceptions.UnknownTimeZoneError:
                logger.warning(f"⚠️ Unknown timezone {user_timezone} for user {user_id}, using UTC")
                tz = pytz.UTC
                user_timezone = "UTC"
            
            # Get current time in user timezone
            now_utc = datetime.now(pytz.UTC)
            now_user = now_utc.astimezone(tz)
            today_user = now_user.date()
            logger.debug(f"Current time in user timezone: {now_user}")
            
            messages_to_create = []
            
            # 1. Fixed Affirmation Messages (3 messages)
            fixed_messages = [
                {
                    "message_type": "daily_affirmation",
                    "time_key": "morning_positivity",
                    "default_time": "08:00"
                },
                {
                    "message_type": "midday_boost", 
                    "time_key": "midday_positivity",
                    "default_time": "12:00"
                },
                {
                    "message_type": "evening_wind_down",
                    "time_key": "afternoon_positivity", 
                    "default_time": "16:00"
                }
            ]
            
            for msg in fixed_messages:
                time_str = subscriber.get(msg["time_key"], msg["default_time"])
                scheduled_time = self._calculate_next_daily_occurrence(today_user, time_str, tz)
                next_iso = scheduled_time.isoformat()
                if not self._exists_scheduled_message(user_id, msg["message_type"], next_iso):
                    messages_to_create.append({
                        "subscriber_id": user_id,
                        "message_type": msg["message_type"],
                        "scheduled_for": next_iso,
                        "status": "pending",
                        "content": ""
                    })
            
            # 2. User-Customized Messages (4 messages with staggered timing)
            customized_messages = [
                {
                    "message_type": "day_planning",
                    "pref_key": "day_planning",
                    "legacy_keys": ["day_planning_time"],
                    "stagger_minutes": 0  # Send at exact user time
                },
                {
                    "message_type": "accountability_checkin",
                    "pref_key": "accountability_checkin", 
                    "legacy_keys": ["accountability_time", "accountability_checkin_time"],
                    "stagger_minutes": 2  # Send 2 minutes after user time
                },
                {
                    "message_type": "gratitude_prompt",
                    "pref_key": "evening_gratitude",
                    "legacy_keys": ["evening_gratitude_time", "gratitude_time"],
                    "stagger_minutes": 4  # Send 4 minutes after user time
                }
            ]
            
            for msg in customized_messages:
                # Try current key format first
                time_str = preferences.get(msg["pref_key"])
                
                # If not found, try legacy key formats for backward compatibility
                if not time_str:
                    for legacy_key in msg.get("legacy_keys", []):
                        time_str = preferences.get(legacy_key)
                        if time_str:
                            logger.info(f"Found time using legacy key {legacy_key}: {time_str} for user {user_id}")
                            break
                
                if time_str:
                    logger.info(f"✅ Found {msg['message_type']} time: {time_str}")
                    # Parse AM/PM format to 24-hour
                    parsed_time = self._parse_ampm_time(time_str)
                    if parsed_time:
                        scheduled_time = self._calculate_next_daily_occurrence(today_user, parsed_time, tz)
                        
                        # Apply staggering to reduce simultaneous message bursts
                        stagger_minutes = msg.get("stagger_minutes", 0)
                        if stagger_minutes > 0:
                            scheduled_time = scheduled_time + timedelta(minutes=stagger_minutes)
                            logger.debug(f"Applied {stagger_minutes}min stagger to {msg['message_type']}")
                        
                        next_iso = scheduled_time.isoformat()
                        if not self._exists_scheduled_message(user_id, msg["message_type"], next_iso):
                            messages_to_create.append({
                                "subscriber_id": user_id,
                                "message_type": msg["message_type"],
                                "scheduled_for": next_iso,
                                "status": "pending",
                                "content": ""
                            })
                    else:
                        logger.warning(f"⚠️ Could not parse time '{time_str}' for {msg['message_type']}")
                else:
                    logger.warning(f"❌ No time found for {msg['message_type']} (looked for keys: {[msg['pref_key']] + msg.get('legacy_keys', [])})")
            
            # 3. Weekly Reflection Message
            weekly_reflection = preferences.get("weekly_reflection")
            
            # Try legacy key if current key not found
            if not weekly_reflection:
                weekly_reflection = preferences.get("weekly_reflection_schedule")
                if weekly_reflection:
                    logger.info(f"Found weekly_reflection using legacy key 'weekly_reflection_schedule' for user {user_id}")
            
            # Handle both dict format and legacy string format  
            day_raw = None
            time_raw = None
            
            if weekly_reflection:
                if isinstance(weekly_reflection, dict):
                    # Modern dict format: {"day": "sunday", "time": "11:00 AM"}
                    day_raw = weekly_reflection.get("day", "sunday")
                    time_raw = weekly_reflection.get("time", "11:00 AM")
                    logger.info(f"✅ Found weekly_reflection (dict format): day='{day_raw}', time='{time_raw}'")
                elif isinstance(weekly_reflection, str):
                    # Legacy string format: "wednsday 11:16am" or "sunday 10:30am"
                    logger.info(f"✅ Found weekly_reflection (legacy string format): '{weekly_reflection}'")
                    parts = weekly_reflection.strip().split(None, 1)  # Split on whitespace, max 2 parts
                    if len(parts) >= 2:
                        day_raw = parts[0]
                        time_raw = parts[1]
                        logger.info(f"✅ Parsed legacy string: day='{day_raw}', time='{time_raw}'")
                    elif len(parts) == 1:
                        # Only day provided in legacy format, use default time
                        day_raw = parts[0]
                        time_raw = "11:00 AM"
                        logger.info(f"✅ Parsed legacy string (day only): day='{day_raw}', using default time='{time_raw}'")
                    else:
                        logger.warning(f"⚠️ Could not parse legacy weekly_reflection string: '{weekly_reflection}'")
            
            if day_raw and time_raw:
                # Normalize day name (handles "wednsday" → "wednesday", "thuesday" → "tuesday")
                day = self._normalize_weekday(day_raw)
                parsed_time = self._parse_ampm_time(time_raw)
                
                if parsed_time:
                    scheduled_time = self._calculate_next_weekly_occurrence(today_user, day, parsed_time, tz)
                    next_iso = scheduled_time.isoformat()
                    if not self._exists_scheduled_message(user_id, "weekly_reflection", next_iso):
                        messages_to_create.append({
                            "subscriber_id": user_id,
                            "message_type": "weekly_reflection",
                            "scheduled_for": next_iso,
                            "status": "pending",
                            "content": ""
                        })
                        logger.info(f"✅ Created weekly reflection for {user_id}: {day} at {time_raw} (next: {next_iso})")
                    else:
                        logger.info(f"🔄 Weekly reflection already exists for {user_id} at {next_iso}")
                else:
                    logger.warning(f"⚠️ Could not parse weekly_reflection time '{time_raw}' for user {user_id}")
            else:
                logger.warning(f"❌ No valid weekly_reflection found for user {user_id} (value: {weekly_reflection})")
            
            # Batch insert all scheduled messages
            if messages_to_create:
                logger.info(f"📝 Creating {len(messages_to_create)} scheduled messages")
                logger.debug(f"Messages to create: {[msg['message_type'] for msg in messages_to_create]}")
                
                try:
                    result = self.client.table("scheduled_messages") \
                        .insert(messages_to_create) \
                        .execute()
                    
                    created_count = len(result.data) if result.data else 0
                    logger.info(f"✅ Successfully created {created_count} scheduled messages for user {user_id}")
                    return True
                    
                except Exception as e:
                    error_msg = str(e).lower()
                    if "unique" in error_msg or "duplicate" in error_msg or "constraint" in error_msg:
                        # Database unique constraint caught duplicates - this is expected and safe
                        logger.info(f"🔒 Duplicate messages prevented by database constraint for user {user_id}")
                        return True  # Consider this success - duplicates were properly prevented
                    else:
                        # Real error - log and fail
                        logger.error(f"❌ Failed to create scheduled messages for user {user_id}: {e}")
                        return False
            else:
                logger.warning(f"⚠️ No scheduled messages created for user {user_id} - missing preferences")
                logger.debug(f"Preferences available: {list(preferences.keys())}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error creating scheduled messages for user {user_id}: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False
    
    def _parse_ampm_time(self, time_str: str) -> str:
        """
        Parse time in various formats to 24-hour format
        Accepts: '7:03am', '7:03 am', '7am', '07:03', '19:10', '7'
        Returns: 'HH:MM' or None
        """
        import re
        
        if not time_str:
            return None
            
        s = time_str.strip().lower()
        
        try:
            # 24-hour 'HH:MM' format
            m24 = re.fullmatch(r'([01]?\d|2[0-3]):([0-5]\d)', s)
            if m24:
                return f"{int(m24.group(1)):02d}:{int(m24.group(2)):02d}"

            # 12-hour variants: 'h', 'h:mm', 'h:mm:ss', optional space, optional a|am|p|pm
            m12 = re.fullmatch(r'(\d{1,2})(?::([0-5]\d))?(?::([0-5]\d))?\s*(a|am|p|pm)?', s)
            if m12:
                h = int(m12.group(1))
                m = int(m12.group(2) or 0)
                # Skip seconds (group 3) for time calculation
                suf = (m12.group(4) or "").lower()

                if suf:  # 12h with am/pm
                    if not (1 <= h <= 12):
                        return None
                    if suf in ("p", "pm") and h != 12:
                        h += 12
                    if suf in ("a", "am") and h == 12:
                        h = 0
                    return f"{h:02d}:{m:02d}"
                else:
                    # No suffix -> treat as 24h hour only, e.g., '7' -> 07:00
                    if 0 <= h <= 23 and 0 <= m <= 59:
                        return f"{h:02d}:{m:02d}"

            logger.warning("Could not parse time format: %s", time_str)
            return None
            
        except Exception as e:
            logger.error("Error parsing time %s: %s", time_str, str(e))
            return None
    
    def _normalize_weekday(self, s: str) -> str:
        """AI-powered weekday normalization that handles any typo or abbreviation"""
        if not s:
            return "sunday"  # Default fallback
            
        s = s.strip().lower()
        
        # Quick exact matches for common cases (performance optimization)
        _EXACT_MATCHES = {
            "monday": "monday", "mon": "monday",
            "tuesday": "tuesday", "tue": "tuesday", "tues": "tuesday", 
            "wednesday": "wednesday", "wed": "wednesday", "weds": "wednesday",
            "thursday": "thursday", "thu": "thursday", "thur": "thursday", "thurs": "thursday",
            "friday": "friday", "fri": "friday",
            "saturday": "saturday", "sat": "saturday",
            "sunday": "sunday", "sun": "sunday",
        }
        
        if s in _EXACT_MATCHES:
            return _EXACT_MATCHES[s]
            
        # Use AI for typo detection and correction
        try:
            from openai import OpenAI
            from app.config import settings
            
            client = OpenAI(api_key=settings.OPENAI_API_KEY)
            
            prompt = f"""
Given this potentially misspelled weekday: "{s}"

Return ONLY the correct weekday name in lowercase.

Examples:
- "wednsday" → "wednesday"
- "thuesday" → "tuesday" 
- "munday" → "monday"
- "teusday" → "tuesday"
- "wendsday" → "wednesday"
- "thursady" → "thursday"
- "fryday" → "friday"
- "saterday" → "saturday"
- "sundaay" → "sunday"

If it's clearly not a weekday, return "sunday" as default.
Return ONLY the weekday name, nothing else.
"""

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert at correcting weekday spelling mistakes. Return only the corrected weekday name."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=10,
                temperature=0.1
            )
            
            result = response.choices[0].message.content.strip().lower()
            
            # Validate result is a real weekday
            valid_weekdays = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
            if result in valid_weekdays:
                if result != s:  # Only log if correction was made
                    logger.info(f"AI corrected weekday: '{s}' → '{result}'")
                return result
            else:
                logger.warning(f"AI returned invalid weekday '{result}' for input '{s}', using 'sunday'")
                return "sunday"
                
        except Exception as e:
            logger.warning(f"AI weekday normalization failed for '{s}': {e}, using fallback")
            
            # Fallback to difflib for offline capability
            import difflib
            _WEEKDAY_CANON = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
            match = difflib.get_close_matches(s, _WEEKDAY_CANON, n=1, cutoff=0.6)
            return match[0] if match else "sunday"
    
    def _calculate_next_daily_occurrence(self, today, time_str: str, tz) -> datetime:
        """Calculate next occurrence of daily time in user timezone"""
        try:
            hour, minute = map(int, time_str.split(":"))
            
            # Create datetime for today at specified time
            target_time = tz.localize(datetime.combine(today, datetime.min.time().replace(hour=hour, minute=minute)))
            
            # If time has already passed today, schedule for tomorrow
            now_tz = datetime.now(tz)
            if target_time <= now_tz:
                target_time += timedelta(days=1)
            
            # Convert to UTC for database storage
            return target_time.astimezone(pytz.UTC)
            
        except Exception as e:
            logger.error(f"Error calculating daily occurrence for {time_str}: {e}")
            # Fallback: schedule for next hour
            return datetime.now(pytz.UTC) + timedelta(hours=1)
    
    def _calculate_next_weekly_occurrence(self, today, day_name: str, time_str: str, tz) -> datetime:
        """
        Calculate next occurrence of weekly time in user timezone.
        If the day is today and target time hasn't passed yet → schedule today.
        Otherwise → schedule the next week's occurrence.
        """
        try:
            # Map day names to weekday numbers (Monday=0, Sunday=6) - matches datetime.weekday()
            day_mapping = {
                "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
                "friday": 4, "saturday": 5, "sunday": 6
            }
            
            target_weekday = day_mapping.get(day_name.lower(), 6)  # Default to Sunday
            current_weekday = today.weekday()
            
            # Parse HH:MM (already normalized by _parse_ampm_time)
            hour, minute = map(int, time_str.split(":"))
            
            # Compute base days_ahead using modulo arithmetic (0..6)
            days_ahead = (target_weekday - current_weekday) % 7  # 0 means "today"
            
            # Build candidate datetime in user's timezone
            target_date = today + timedelta(days=days_ahead)
            candidate_local = tz.localize(datetime.combine(target_date, datetime.min.time().replace(hour=hour, minute=minute)))
            
            # If today and time already passed, bump one week (same logic as daily scheduling)
            now_local = datetime.now(tz)
            if days_ahead == 0 and candidate_local <= now_local:
                candidate_local += timedelta(days=7)
            
            # Convert to UTC for database storage
            return candidate_local.astimezone(pytz.UTC)
            
        except Exception as e:
            logger.error(f"Error calculating weekly occurrence for {day_name} {time_str}: {e}")
            # Fallback: schedule for next Sunday at noon
            return datetime.now(pytz.UTC) + timedelta(days=7)

    async def populate_scheduled_messages_from_preferences(self) -> int:
        """Migration utility: populate scheduled_messages from user preferences"""
        try:
            # Get all active subscribers with completed onboarding
            result = self.client.table("subscribers") \
                .select("id, current_timezone, preferences") \
                .eq("status", "active") \
                .filter("preferences->>onboarding_completed", "eq", "true") \
                .execute()
            
            migrated_count = 0
            
            for subscriber in result.data:
                user_id = subscriber["id"]
                
                # Check if user already has scheduled messages
                existing_messages = self.client.table("scheduled_messages") \
                    .select("id") \
                    .eq("subscriber_id", user_id) \
                    .limit(1) \
                    .execute()
                
                if not existing_messages.data:
                    # Create scheduled messages for this user
                    success = await self.create_scheduled_messages_for_user(user_id)
                    if success:
                        migrated_count += 1
                        logger.info(f"Migrated user {user_id} to scheduled messages")
            
            logger.info(f"Migrated {migrated_count} users to scheduled_messages")
            return migrated_count
            
        except Exception as e:
            logger.error(f"Error populating scheduled messages: {e}")
            return 0

    def _exists_scheduled_message(self, user_id: str, message_type: str, scheduled_iso: str) -> bool:
        """Check if a scheduled message already exists to prevent duplicates"""
        try:
            result = self.client.table("scheduled_messages") \
                .select("id") \
                .eq("subscriber_id", user_id) \
                .eq("message_type", message_type) \
                .eq("scheduled_for", scheduled_iso) \
                .in_("status", ["pending", "queued"]) \
                .limit(1) \
                .execute()
            return bool(result.data)
        except Exception:
            return False

    async def create_immediate_test_messages(self, user_id: str) -> bool:
        """Create immediate test messages for debugging (scheduled 1 minute ago)"""
        try:
            from datetime import datetime, timedelta
            
            # Create messages that are due immediately
            now_minus_1min = datetime.utcnow() - timedelta(minutes=1)
            
            test_messages = [
                {
                    "subscriber_id": user_id,
                    "message_type": "daily_affirmation", 
                    "scheduled_for": now_minus_1min.isoformat() + "+00:00",
                    "status": "pending",
                    "content": ""
                },
                {
                    "subscriber_id": user_id,
                    "message_type": "midday_boost",
                    "scheduled_for": now_minus_1min.isoformat() + "+00:00", 
                    "status": "pending",
                    "content": ""
                },
                {
                    "subscriber_id": user_id,
                    "message_type": "evening_wind_down",
                    "scheduled_for": now_minus_1min.isoformat() + "+00:00",
                    "status": "pending", 
                    "content": ""
                }
            ]
            
            result = self.client.table("scheduled_messages").insert(test_messages).execute()
            created_count = len(result.data) if result.data else 0
            
            logger.info(f"Created {created_count} immediate test messages for user {user_id}")
            return created_count > 0
            
        except Exception as e:
            logger.error(f"Error creating immediate test messages: {e}")
            return False
