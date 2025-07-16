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
import json
import openai

from app.services.supabase_client import SupabaseService
from app.services.timezone_detector import TimezoneDetector
from app.config import settings

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
        self.openai_client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL
        
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
        
        # Question contexts for dynamic LLM generation
        self.question_contexts = {
            OnboardingStep.START: {"type": "morning_affirmation", "emoji": "⏰"},
            OnboardingStep.MORNING_AFFIRMATION: {"type": "day_planning", "emoji": "📝"}, 
            OnboardingStep.DAY_PLANNING: {"type": "midday_motivation", "emoji": "☀️"},
            OnboardingStep.MIDDAY_AFFIRMATION: {"type": "evening_winddown", "emoji": "🌅"},
            OnboardingStep.EVENING_AFFIRMATION: {"type": "progress_checkin", "emoji": "💪"},
            OnboardingStep.ACCOUNTABILITY_CHECKIN: {"type": "bedtime_gratitude", "emoji": "🌙"},
            OnboardingStep.SLEEP_TIME: {"type": "weekly_reflection", "emoji": "🗓️"}
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
            is_valid, parsed_value = await self.process_response(current_step, message)
            
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
                    
                    # Get updated preferences for personalized question
                    updated_preferences = await self.supabase.get_user_preferences(user_id)
                    personalized_question = await self.generate_personalized_question(next_step, updated_preferences)
                    
                    return {
                        "is_onboarding": True,
                        "completed": False,
                        "message": personalized_question
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
            
            # Generate personalized first question
            user_preferences = await self.supabase.get_user_preferences(user_id)
            first_question = await self.generate_personalized_question(OnboardingStep.START, user_preferences)
            
            # Return messages for Celery to send
            return {
                "welcome_message": self.get_welcome_message(),
                "first_question": first_question
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
    
    # ==================== PERSONALIZED QUESTION GENERATION ====================
    
    async def generate_personalized_question(self, step: OnboardingStep, user_preferences: Dict[str, Any]) -> str:
        """Generate personalized onboarding questions based on previous answers"""
        try:
            context = self.question_contexts.get(step)
            if not context:
                return "Please let me know when you'd like this scheduled."
            
            # Build context from previous answers - only include completed steps
            previous_answers = []
            for key, value in user_preferences.items():
                if key.endswith('_affirmation') or key.endswith('_planning') or key.endswith('_checkin'):
                    if value and value != 'null':  # Only include actual values
                        previous_answers.append(f"{key}: {value}")
            
            previous_context = "\n".join(previous_answers) if previous_answers else "This is the first question."
            
            question_prompts = {
                "morning_affirmation": f"""Generate a warm, conversational question asking when the user wants their morning affirmation. 
                Keep it natural and friendly. Start with the emoji ⏰ and make it feel like a personal coach asking.""",
                
                "day_planning": f"""The user wants morning affirmations at {user_preferences.get('morning_affirmation', 'not specified yet')}. 
                Generate a natural follow-up question asking when they'd like to plan their day. Reference their morning time and suggest a logical time after. 
                Start with 📝 and keep it conversational.""",
                
                "midday_motivation": f"""The user plans their day at {user_preferences.get('day_planning', 'not specified yet')}. 
                Generate a question asking when they'd like a midday boost. Reference their morning schedule and suggest a natural lunch-time slot. 
                Start with ☀️ and make it personal.""",
                
                "evening_winddown": f"""The user gets midday motivation at {user_preferences.get('midday_affirmation', 'not specified yet')}. 
                Generate a question asking when they'd like an evening wind-down message. Reference their day flow and suggest early evening. 
                Start with 🌅 and keep it warm.""",
                
                "progress_checkin": f"""The user wants evening wind-down at {user_preferences.get('evening_affirmation', 'not specified yet')}. 
                Generate a question asking when they'd like a progress check-in. Reference their evening time and suggest slightly later. 
                Start with 💪 and make it encouraging.""",
                
                "bedtime_gratitude": f"""The user wants progress check-ins at {user_preferences.get('accountability_checkin', 'not specified yet')}. 
                Generate a question asking about their bedtime for gratitude messages. Reference their evening schedule and suggest before sleep. 
                Start with 🌙 and make it soothing.""",
                
                "weekly_reflection": f"""The user goes to bed around {user_preferences.get('evening_gratitude', 'not specified yet')}. 
                Generate a question asking when they'd like weekly reflection. Suggest a relaxed weekend time. 
                Start with 🗓️ and make it thoughtful."""
            }
            
            prompt = f"""You are a friendly AI coach setting up a user's personalized schedule. 
            
            CONTEXT: {previous_context}
            
            TASK: {question_prompts.get(context['type'], 'Ask about scheduling preferences')}
            
            RULES:
            - Keep it under 25 words
            - Sound natural and conversational, not robotic
            - Reference previous answers when logical
            - Make intelligent suggestions based on their existing schedule
            - Don't use generic examples like "e.g., 7:00 AM"
            - Make it feel like a personal conversation
            
            Generate the question now:"""
            
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=80,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating personalized question: {e}")
            # Fallback to context-appropriate question
            fallback_questions = {
                "morning_affirmation": "⏰ What time would you like your morning affirmation?",
                "day_planning": "📝 When would you like to plan your day?",
                "midday_motivation": "☀️ When would you like a midday motivation boost?",
                "evening_winddown": "🌅 What time would you like your evening wind-down message?",
                "progress_checkin": "💪 When should I check in about your daily progress?",
                "bedtime_gratitude": "🌙 What time do you usually go to bed?",
                "weekly_reflection": "🗓️ Which day and time would you like your weekly reflection?"
            }
            return fallback_questions.get(context['type'], f"{context['emoji']} When would you like this scheduled?")
    
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
    
    async def process_response(self, state: OnboardingStep, user_input: str) -> Tuple[bool, Any]:
        """
        Process user response for the current state using OpenAI for natural language understanding
        Returns: (is_valid, parsed_value)
        """        
        if state in [OnboardingStep.START, OnboardingStep.MORNING_AFFIRMATION, OnboardingStep.DAY_PLANNING,
                     OnboardingStep.MIDDAY_AFFIRMATION, OnboardingStep.EVENING_AFFIRMATION,
                     OnboardingStep.ACCOUNTABILITY_CHECKIN, OnboardingStep.SLEEP_TIME]:
            # Parse time using OpenAI with context awareness
            parsed_time = await self.parse_time(user_input, state)
            if parsed_time:
                # For sleep time, calculate gratitude time (30 minutes earlier)
                if state == OnboardingStep.SLEEP_TIME:
                    parsed_time = self.calculate_gratitude_time(parsed_time)
                return True, parsed_time
            return False, None
            
        elif state == OnboardingStep.WEEKLY_REFLECTION:
            # Parse day and time using OpenAI
            day, time = await self.parse_weekly_time(user_input)
            if day and time:
                return True, {"day": day, "time": time}
            return False, None
        
        return False, None
    
    # ==================== PARSING METHODS ====================
    
    async def parse_time(self, time_str: str, context_step: OnboardingStep = None) -> Optional[str]:
        """Parse time string to 24-hour format using OpenAI with context awareness"""
        try:
            # Build context for intelligent parsing
            context_info = ""
            if context_step:
                if context_step == OnboardingStep.SLEEP_TIME:
                    context_info = "This is for bedtime/sleep, so 11 likely means 11 PM (23:00)"
                elif context_step in [OnboardingStep.START, OnboardingStep.MORNING_AFFIRMATION, OnboardingStep.DAY_PLANNING]:
                    context_info = "This is for morning activities, so times are likely AM (8 = 08:00)"
                elif context_step in [OnboardingStep.EVENING_AFFIRMATION, OnboardingStep.ACCOUNTABILITY_CHECKIN]:
                    context_info = "This is for evening activities, so times are likely PM (7 = 19:00)"
                elif context_step == OnboardingStep.MIDDAY_AFFIRMATION:
                    context_info = "This is for midday/lunch time, so 13 = 13:00 (1 PM), 1 = 13:00"
            
            prompt = f"""
            Parse the following user input into a 24-hour time format (HH:MM).
            
            User input: "{time_str}"
            Context: {context_info}
            
            Instructions:
            - Extract the time from natural language
            - Return only time in HH:MM format (24-hour)
            - Use context to make intelligent assumptions:
              * For sleep/bedtime: "11" = 23:00 (11 PM)
              * For morning activities: "8" = 08:00 (8 AM)  
              * For evening activities: "7" = 19:00 (7 PM)
              * For midday: "1" = 13:00 (1 PM)
            - Handle natural expressions:
              "Let's say at 8" -> "08:00"
              "Something around 1 pm" -> "13:00"  
              "Usually at 11" (bedtime context) -> "23:00"
              "Sunday at 10" -> "10:00"
            
            Return only the time in HH:MM format, nothing else.
            """
            
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=50,
                temperature=0.3
            )
            
            result = response.choices[0].message.content.strip()
            
            # Validate the response format
            if result and re.match(r'^[0-2][0-9]:[0-5][0-9]$', result):
                return result
            
            return None
        except Exception as e:
            logger.error(f"Error parsing time with OpenAI: {e}")
            return None
    
    async def parse_weekly_time(self, message: str) -> Tuple[Optional[str], Optional[str]]:
        """Parse weekly reflection day and time using OpenAI for natural language understanding"""
        try:
            prompt = f"""
            Parse the following user input to extract a day of the week and time for weekly reflection.
            
            User input: "{message}"
            
            Instructions:
            - Extract the day of the week (convert to lowercase)
            - Extract the time in 24-hour format (HH:MM)
            - Return as JSON: {{"day": "dayname", "time": "HH:MM"}}
            - Valid days: monday, tuesday, wednesday, thursday, friday, saturday, sunday
            - If time is ambiguous, make reasonable assumptions based on context
            - Examples:
              "Sunday at 11 is good" -> {{"day": "sunday", "time": "11:00"}}
              "Monday 9am" -> {{"day": "monday", "time": "09:00"}}
              "Friday evening around 7" -> {{"day": "friday", "time": "19:00"}}
              "Sunday 11" -> {{"day": "sunday", "time": "11:00"}}
            
            - For weekly reflection, assume morning times (AM) unless clearly evening context
            - Always return valid JSON with day and time fields
            - If parsing fails, return {{"day": null, "time": null}}
            
            Return only the JSON object, nothing else.
            """
            
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100,
                temperature=0.3
            )
            
            result = response.choices[0].message.content.strip()
            
            # Parse the JSON response
            if result:
                try:
                    data = json.loads(result.strip())
                    day = data.get('day', '').lower()
                    time_str = data.get('time', '')
                    
                    # Handle null values from failed parsing
                    if not day or not time_str or day == 'null' or time_str == 'null':
                        return None, None
                    
                    # Validate day
                    valid_days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
                    if day not in valid_days:
                        return None, None
                    
                    # Validate time format
                    if re.match(r'^[0-2][0-9]:[0-5][0-9]$', time_str):
                        return day, time_str
                    
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON response from OpenAI: {result}")
            
            return None, None
        except Exception as e:
            logger.error(f"Error parsing weekly time with OpenAI: {e}")
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