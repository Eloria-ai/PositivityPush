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
        """Get subscribers ready for daily messages based on timezone"""
        try:
            query = self.client.table("subscribers").select("*").eq("status", "active")
            
            if timezone:
                query = query.eq("timezone", timezone)
            
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
                query = query.filter("preferences->>timezone", "eq", timezone)
            
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