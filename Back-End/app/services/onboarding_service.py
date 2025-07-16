"""
Interactive Onboarding Service for Positivity Push
Collects user preferences for personalized scheduling through WhatsApp conversation
Uses async webhook + Celery architecture for reliable message delivery
"""

import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import re
from enum import Enum

from app.services.supabase_client import SupabaseService
from app.services.timezone_detector import TimezoneDetector

logger = logging.getLogger(__name__)

class OnboardingStep(Enum):
    """Steps in the onboarding conversation"""
    START = "start"
    MORNING_AFFIRMATION = "morning_affirmation" 
    DAY_PLANNING = "day_planning"
    MIDDAY_AFFIRMATION = "midday_affirmation"
    EVENING_AFFIRMATION = "evening_affirmation"
    ACCOUNTABILITY_CHECKIN = "accountability_checkin"
    SLEEP_TIME = "sleep_time"
    WEEKLY_REFLECTION = "weekly_reflection"
    COMPLETED = "completed"

class OnboardingService:
    """
    Handles interactive onboarding conversation for new users
    Uses async webhook + Celery architecture for reliable message delivery
    """
    
    def __init__(self, supabase_service: SupabaseService):
        self.supabase = supabase_service
        self.timezone_detector = TimezoneDetector()
        
        # Conversation flow mapping
        self.step_flow = {
            OnboardingStep.START: OnboardingStep.MORNING_AFFIRMATION,
            OnboardingStep.MORNING_AFFIRMATION: OnboardingStep.DAY_PLANNING,
            OnboardingStep.DAY_PLANNING: OnboardingStep.MIDDAY_AFFIRMATION,
            OnboardingStep.MIDDAY_AFFIRMATION: OnboardingStep.EVENING_AFFIRMATION,
            OnboardingStep.EVENING_AFFIRMATION: OnboardingStep.ACCOUNTABILITY_CHECKIN,
            OnboardingStep.ACCOUNTABILITY_CHECKIN: OnboardingStep.SLEEP_TIME,
            OnboardingStep.SLEEP_TIME: OnboardingStep.WEEKLY_REFLECTION,
            OnboardingStep.WEEKLY_REFLECTION: OnboardingStep.COMPLETED
        }
        
        # Questions for each step
        self.questions = {
            OnboardingStep.START: "⏰ What time would you like to receive your **morning affirmation**? (e.g., 7:00 AM, 8:30 AM)",
            OnboardingStep.MORNING_AFFIRMATION: "📝 What time do you prefer to **plan your day**? (e.g., 8:00 AM, 9:00 AM)",
            OnboardingStep.DAY_PLANNING: "☀️ When would you like a **midday motivation boost**? (e.g., 12:00 PM, 1:00 PM)",
            OnboardingStep.MIDDAY_AFFIRMATION: "🌅 What time would you like your **evening wind-down message**? (e.g., 6:00 PM, 7:00 PM)",
            OnboardingStep.EVENING_AFFIRMATION: "💪 When should I **check in about your daily progress**? (e.g., 7:00 PM, 8:00 PM)",
            OnboardingStep.ACCOUNTABILITY_CHECKIN: "🌙 Around what time do you usually **go to bed**? (This helps time your gratitude message, e.g., 9:00 PM, 10:30 PM)",
            OnboardingStep.SLEEP_TIME: "🗓️ Which **day and time** would you like your weekly reflection? (e.g., Sunday 10:00 AM, Monday 9:00 AM)"
        }
        
        # Clarification messages
        self.clarifications = {
            OnboardingStep.START: "Please enter a valid time like '7:00 AM' or '7 morning'",
            OnboardingStep.MORNING_AFFIRMATION: "Please enter a valid time like '7:00 AM' or '07:30'",
            OnboardingStep.DAY_PLANNING: "Please enter a valid time like '8:00 AM' or '08:30'",
            OnboardingStep.MIDDAY_AFFIRMATION: "Please enter a valid time like '12:00 PM' or '13:00'",
            OnboardingStep.EVENING_AFFIRMATION: "Please enter a valid time like '6:00 PM' or '18:00'",
            OnboardingStep.ACCOUNTABILITY_CHECKIN: "Please enter a valid time like '7:00 PM' or '19:00'",
            OnboardingStep.SLEEP_TIME: "Please enter a valid time like '9:00 PM' or '21:30'",
            OnboardingStep.WEEKLY_REFLECTION: "Please enter day and time like 'Sunday 10:00 AM' or 'Monday 9:00'"
        }
        
        # Preference keys for database storage
        self.preference_keys = {
            OnboardingStep.START: "morning_affirmation",  # START question asks for morning time
            OnboardingStep.MORNING_AFFIRMATION: "morning_affirmation",
            OnboardingStep.DAY_PLANNING: "day_planning",
            OnboardingStep.MIDDAY_AFFIRMATION: "midday_affirmation",
            OnboardingStep.EVENING_AFFIRMATION: "evening_affirmation",
            OnboardingStep.ACCOUNTABILITY_CHECKIN: "accountability_checkin",
            OnboardingStep.SLEEP_TIME: "evening_gratitude",  # Gratitude before sleep
            OnboardingStep.WEEKLY_REFLECTION: "weekly_reflection"
        }
    
    # ==================== CORE ASYNC METHODS ====================
    
    async def process_webhook_message(self, user_id: str, wa_id: str, message: str) -> Dict[str, Any]:
        """
        Process incoming webhook message during onboarding
        Returns state change info for Celery task enqueuing
        """
        try:
            # Get current onboarding state
            preferences = await self.supabase.get_user_preferences(user_id)
            current_step_str = preferences.get("onboarding_step")
            
            if not current_step_str:
                return {"is_onboarding": False}
            
            try:
                current_step = OnboardingStep(current_step_str)
            except ValueError:
                logger.error(f"Invalid onboarding step: {current_step_str}")
                return {"is_onboarding": False}
            
            # Process user response
            is_valid, parsed_value = self.process_response(current_step, message)
            
            if is_valid:
                # Save the parsed value to preferences
                preference_key = self.preference_keys.get(current_step)
                if preference_key:
                    await self.supabase.set_preference_value(user_id, preference_key, parsed_value)
                
                # Get next step
                next_step = self.step_flow.get(current_step)
                
                if next_step == OnboardingStep.COMPLETED:
                    # Complete onboarding
                    await self.supabase.mark_onboarding_completed(user_id)
                    await self.supabase.set_preference_value(user_id, "onboarding_step", None)
                    
                    return {
                        "is_onboarding": True,
                        "completed": True,
                        "message": self.get_completion_message()
                    }
                else:
                    # Move to next step
                    await self.supabase.set_preference_value(user_id, "onboarding_step", next_step.value)
                    
                    return {
                        "is_onboarding": True,
                        "completed": False,
                        "message": self.questions.get(next_step)
                    }
            else:
                # Invalid response - ask for clarification
                clarification = self.clarifications.get(current_step, "Please try again.")
                return {
                    "is_onboarding": True,
                    "completed": False,
                    "message": f"🤔 {clarification}"
                }
                
        except Exception as e:
            logger.error(f"Error processing onboarding message: {e}")
            return {"is_onboarding": False}
    
    async def start_onboarding(self, user_id: str, client_ip: str = None) -> Dict[str, Any]:
        """
        Start onboarding flow - returns messages to enqueue
        Automatically detects timezone from IP address
        """
        try:
            # Detect timezone automatically
            if client_ip:
                detected_timezone = self.timezone_detector.detect_timezone_from_ip(client_ip)
                logger.info(f"Detected timezone for user {user_id}: {detected_timezone}")
                
                # Set timezone immediately
                await self.supabase.set_preference_value(user_id, "timezone", detected_timezone)
            
            # Set initial state to START step
            await self.supabase.set_preference_value(user_id, "onboarding_step", OnboardingStep.START.value)
            
            # Return messages for Celery to send
            return {
                "welcome_message": self.get_welcome_message(),
                "first_question": self.questions.get(OnboardingStep.START)
            }
            
        except Exception as e:
            logger.error(f"Error starting onboarding: {e}")
            return {}
    
    async def is_user_in_onboarding(self, user_id: str) -> bool:
        """Check if user is currently in onboarding process"""
        try:
            preferences = await self.supabase.get_user_preferences(user_id)
            onboarding_step = preferences.get("onboarding_step")
            return onboarding_step is not None
        except Exception as e:
            logger.error(f"Error checking onboarding status: {e}")
            return False
    
    # ==================== UTILITY METHODS ====================
    
    def get_welcome_message(self) -> str:
        """Get the initial welcome message"""
        return (
            "🎉 Welcome to Positivity Push! I'm excited to be your personal AI coach.\n\n"
            "To give you the best experience, I need to learn about your daily schedule. "
            "This will only take 2-3 minutes and helps me send messages at perfect times for you.\n\n"
            "Ready to get started? ✨"
        )
    
    def get_completion_message(self) -> str:
        """Get the completion message"""
        return (
            "🎉 Perfect! Your personalized schedule is all set up!\n\n"
            "I'll now send you perfectly timed messages based on your preferences. "
            "You can always chat with me anytime for support, motivation, or just to talk.\n\n"
            "Your coaching journey starts now! 🚀\n\n"
            "✨ *Let's make every day a little brighter together!*"
        )
    
    def process_response(self, state: OnboardingStep, user_input: str) -> Tuple[bool, Any]:
        """
        Process user response for the current state
        Returns: (is_valid, parsed_value)
        """
        user_input = user_input.strip().lower()
        
        if state in [OnboardingStep.START, OnboardingStep.MORNING_AFFIRMATION, OnboardingStep.DAY_PLANNING,
                     OnboardingStep.MIDDAY_AFFIRMATION, OnboardingStep.EVENING_AFFIRMATION,
                     OnboardingStep.ACCOUNTABILITY_CHECKIN, OnboardingStep.SLEEP_TIME]:
            # Parse time
            parsed_time = self.parse_time(user_input)
            if parsed_time:
                # For sleep time, calculate gratitude time (30 minutes earlier)
                if state == OnboardingStep.SLEEP_TIME:
                    parsed_time = self.calculate_gratitude_time(parsed_time)
                return True, parsed_time
            return False, None
            
        elif state == OnboardingStep.WEEKLY_REFLECTION:
            # Parse day and time
            day, time = self.parse_weekly_time(user_input)
            if day and time:
                return True, {"day": day, "time": time}
            return False, None
        
        return False, None
    
    # ==================== PARSING METHODS ====================
    
    def parse_time(self, time_str: str) -> Optional[str]:
        """Parse time string to 24-hour format with natural language support"""
        try:
            # Clean the input
            time_str = time_str.lower().strip()
            
            # Remove common words
            time_str = re.sub(r'\b(at|around|about|in|the)\b', '', time_str).strip()
            
            # Handle natural language patterns
            natural_patterns = [
                # Natural morning/evening expressions
                (r'(\d{1,2})\s*(in\s+the\s+)?morning', r'\1 am'),
                (r'(\d{1,2})\s*(in\s+the\s+)?evening', r'\1 pm'),
                (r'(\d{1,2})\s*(in\s+the\s+)?afternoon', r'\1 pm'),
                (r'(\d{1,2})\s*(in\s+the\s+)?night', r'\1 pm'),
                # Handle "7 o'clock" format
                (r'(\d{1,2})\s*o\'?clock', r'\1:00'),
                # Handle "11 am" without colon - more flexible
                (r'(\d{1,2})\s+(am|pm)', r'\1:00 \2'),
            ]
            
            for pattern, replacement in natural_patterns:
                time_str = re.sub(pattern, replacement, time_str)
            
            # Enhanced patterns for various time formats
            patterns = [
                r'(\d{1,2}):(\d{2})\s*(am|pm)',  # 7:30 AM
                r'(\d{1,2}):(\d{1,2})\s*(am|pm)', # 7:0 AM  
                r'(\d{1,2}):00\s*(am|pm)',       # 7:00 AM
                r'(\d{1,2})\s*(am|pm)',          # 7 AM
                r'(\d{1,2}):(\d{2})',            # 07:30 (24h)
                r'(\d{1,2})\.(\d{2})',           # 7.30
                r'(\d{1,2})h(\d{2})',            # 7h30
                r'(\d{1,2})',                    # Just number (assume am if < 12, pm if > 12)
            ]
            
            for pattern in patterns:
                match = re.search(pattern, time_str)
                if match:
                    if len(match.groups()) >= 3:  # AM/PM format
                        hour = int(match.group(1))
                        minute = int(match.group(2)) if match.group(2) else 0
                        period = match.group(3).lower()
                        
                        if period == 'pm' and hour != 12:
                            hour += 12
                        elif period == 'am' and hour == 12:
                            hour = 0
                    elif len(match.groups()) == 2:  # 24-hour format
                        hour = int(match.group(1))
                        minute = int(match.group(2)) if match.group(2) else 0
                    else:  # Just hour number
                        hour = int(match.group(1))
                        minute = 0
                        # Smart assumption: if <= 12, could be AM or PM (default AM)
                        # if > 12, it's 24-hour format
                        if hour <= 12:
                            # Default to AM for morning hours
                            pass
                        elif hour > 12 and hour <= 23:
                            # It's already 24-hour
                            pass
                        else:
                            return None
                    
                    if 0 <= hour <= 23 and 0 <= minute <= 59:
                        return f"{hour:02d}:{minute:02d}"
            
            return None
        except Exception:
            return None
    
    def parse_weekly_time(self, message: str) -> Tuple[Optional[str], Optional[str]]:
        """Parse weekly reflection day and time with improved natural language support"""
        try:
            message_lower = message.lower().strip()
            
            # Days mapping
            days = {
                'monday': 'monday', 'mon': 'monday',
                'tuesday': 'tuesday', 'tue': 'tuesday', 'tues': 'tuesday',
                'wednesday': 'wednesday', 'wed': 'wednesday',
                'thursday': 'thursday', 'thu': 'thursday', 'thurs': 'thursday',
                'friday': 'friday', 'fri': 'friday',
                'saturday': 'saturday', 'sat': 'saturday',
                'sunday': 'sunday', 'sun': 'sunday'
            }
            
            # Find day with word boundary matching
            day = None
            for day_key, day_value in days.items():
                if re.search(r'\b' + day_key + r'\b', message_lower):
                    day = day_value
                    break
            
            # Extract time using improved parsing
            time_24h = self.parse_time(message_lower)
            
            return day, time_24h
        except Exception:
            return None, None
    
    def parse_timezone(self, timezone_str: str) -> Optional[str]:
        """Parse and validate timezone"""
        timezone_str = timezone_str.strip().upper()
        
        # Common timezone mappings
        timezone_map = {
            'EST': 'EST', 'EASTERN': 'EST', 'ET': 'EST',
            'CST': 'CST', 'CENTRAL': 'CST', 'CT': 'CST',
            'MST': 'MST', 'MOUNTAIN': 'MST', 'MT': 'MST',
            'PST': 'PST', 'PACIFIC': 'PST', 'PT': 'PST',
            'UTC': 'UTC', 'GMT': 'UTC', 'COORDINATED UNIVERSAL TIME': 'UTC',
            'CET': 'CET', 'CENTRAL EUROPEAN': 'CET',
            'BST': 'BST', 'BRITISH': 'BST',
            'JST': 'JST', 'JAPAN': 'JST',
            'AEST': 'AEST', 'AUSTRALIAN': 'AEST'
        }
        
        # Direct match
        if timezone_str in timezone_map:
            return timezone_map[timezone_str]
        
        # City-based detection
        city_zones = {
            'NEW YORK': 'EST', 'BOSTON': 'EST', 'MIAMI': 'EST',
            'CHICAGO': 'CST', 'DALLAS': 'CST', 'HOUSTON': 'CST',
            'DENVER': 'MST', 'PHOENIX': 'MST',
            'LOS ANGELES': 'PST', 'SAN FRANCISCO': 'PST', 'SEATTLE': 'PST',
            'LONDON': 'GMT', 'PARIS': 'CET', 'BERLIN': 'CET', 'ROME': 'CET',
            'TOKYO': 'JST', 'SYDNEY': 'AEST'
        }
        
        for city, zone in city_zones.items():
            if city in timezone_str:
                return zone
        
        # If no match found, return UTC as fallback
        return 'UTC'
    
    def calculate_gratitude_time(self, sleep_time: str) -> str:
        """Calculate gratitude time (30 minutes before sleep)"""
        try:
            hour, minute = map(int, sleep_time.split(':'))
            
            # Subtract 30 minutes
            minute -= 30
            if minute < 0:
                minute += 60
                hour -= 1
            if hour < 0:
                hour += 24
            
            return f"{hour:02d}:{minute:02d}"
        except Exception:
            return sleep_time  # Fallback to original time