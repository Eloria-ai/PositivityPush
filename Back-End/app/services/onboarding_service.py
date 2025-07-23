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
from app.services.timezone_service import TimezoneService
from app.config import settings

logger = logging.getLogger(__name__)

class OnboardingStep(Enum):
    """Steps in the onboarding conversation"""
    START = "start"
    # DEPRECATED: MORNING_AFFIRMATION, MIDDAY_AFFIRMATION, EVENING_AFFIRMATION - now use fixed times (08:00, 12:00, 16:00)
    DAY_PLANNING = "day_planning"
    ACCOUNTABILITY_CHECKIN = "accountability_checkin"
    SLEEP_TIME = "sleep_time"
    WEEKLY_REFLECTION = "weekly_reflection"
    TIMEZONE_LOCATION = "timezone_location"
    COMPLETED = "completed"

class OnboardingService:
    """
    Handles interactive onboarding conversation for new users
    Uses async webhook + Celery architecture for reliable message delivery
    """
    
    def __init__(self, supabase_service: SupabaseService):
        self.supabase = supabase_service
        self.timezone_service = TimezoneService()
        self.openai_client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL
        
        # Conversation flow mapping - affirmation times are now fixed (08:00, 12:00, 16:00)
        self.step_flow = {
            OnboardingStep.START: OnboardingStep.DAY_PLANNING,
            OnboardingStep.DAY_PLANNING: OnboardingStep.ACCOUNTABILITY_CHECKIN,
            OnboardingStep.ACCOUNTABILITY_CHECKIN: OnboardingStep.SLEEP_TIME,
            OnboardingStep.SLEEP_TIME: OnboardingStep.WEEKLY_REFLECTION,
            OnboardingStep.WEEKLY_REFLECTION: OnboardingStep.TIMEZONE_LOCATION,
            OnboardingStep.TIMEZONE_LOCATION: OnboardingStep.COMPLETED
        }
        
        # Question contexts for dynamic LLM generation
        self.question_contexts = {
            OnboardingStep.START: {"type": "day_planning", "emoji": "📝"},
            OnboardingStep.DAY_PLANNING: {"type": "progress_checkin", "emoji": "💪"},
            OnboardingStep.ACCOUNTABILITY_CHECKIN: {"type": "bedtime_gratitude", "emoji": "🌙"},
            OnboardingStep.SLEEP_TIME: {"type": "weekly_reflection", "emoji": "🗓️"},
            OnboardingStep.TIMEZONE_LOCATION: {"type": "timezone_location", "emoji": "🌍"}
        }
        
        # Clarification messages
        self.clarifications = {
            OnboardingStep.START: "Please enter a valid time like '8:00 AM' or '8 morning'",
            OnboardingStep.DAY_PLANNING: "Please enter a valid time like '8:00 AM' or '08:30'",
            OnboardingStep.ACCOUNTABILITY_CHECKIN: "Please enter a valid time like '7:00 PM' or '19:00'",
            OnboardingStep.SLEEP_TIME: "Please enter a valid time like '9:00 PM' or '21:30'",
            OnboardingStep.WEEKLY_REFLECTION: "Please specify AM or PM! For example: 'Sunday 11:00 AM' or 'Sunday 11:00 PM'",
            OnboardingStep.TIMEZONE_LOCATION: "🕒 We respect your privacy and never track your location.\nWhat timezone are you in? (e.g. Africa/Casablanca or Europe/Amsterdam)\nIf you move later, just tell me—like 'I'm in London now'—and I'll adjust automatically."
        }
        
        # Preference keys for database storage - maps each step to what it collects
        self.preference_keys = {
            OnboardingStep.START: "day_planning",  # START step asks for day planning time
            OnboardingStep.DAY_PLANNING: "accountability_checkin",  # DAY_PLANNING step asks for accountability time
            OnboardingStep.ACCOUNTABILITY_CHECKIN: "evening_gratitude",  # ACCOUNTABILITY step asks for sleep/gratitude time
            OnboardingStep.SLEEP_TIME: "weekly_reflection",  # SLEEP_TIME step asks for weekly reflection
            OnboardingStep.WEEKLY_REFLECTION: "current_timezone",  # WEEKLY_REFLECTION step asks for timezone
            OnboardingStep.TIMEZONE_LOCATION: "current_timezone"  # Fallback (should not be used)
        }
    
    # ==================== CORE ASYNC METHODS ====================
    
    async def set_default_affirmation_times(self, user_id: str) -> None:
        """
        Write the fixed affirmation schedule (08:00, 12:00, 16:00) to the subscription.
        """
        try:
            await self.supabase.update_subscription(
                user_id,
                {
                    "morning_positivity": "08:00",
                    "midday_positivity": "12:00",
                    "afternoon_positivity": "16:00",
                },
            )
            logger.info(f"Default affirmation times set for user {user_id}")
        except Exception as e:
            logger.error(f"Error setting default affirmation times for {user_id}: {e}")
    
    async def process_webhook_message(self, user_id: str, wa_id: str, message: str) -> Dict[str, Any]:
        """
        Process incoming webhook message during conversational onboarding
        Returns state change info for Celery task enqueuing
        """
        try:
            # Get current onboarding state
            preferences = await self.supabase.get_user_preferences(user_id)
            onboarding_completed = preferences.get("onboarding_completed", True)
            onboarding_step = preferences.get("onboarding_step")
            
            logger.debug(f"User {user_id}: completed={onboarding_completed} (type: {type(onboarding_completed)}), step={onboarding_step}")
            logger.debug(f"Full preferences: {preferences}")
            
            # Reset onboarding for testing if user says "reset" or "restart"
            if message.lower().strip() in ["reset", "restart", "start over"]:
                logger.info(f"Resetting onboarding for user {user_id}")
                # Batch update all reset preferences in single DB call
                reset_updates = {
                    "onboarding_completed": False,
                    "onboarding_step": "start",
                    "day_planning": None,
                    "accountability_checkin": None,
                    "evening_gratitude": None,
                    "weekly_reflection": None
                }
                await self.supabase.batch_update_preferences(user_id, reset_updates)
                # Update the preferences object to reflect the reset
                preferences.update(reset_updates)
                onboarding_completed = False
            
            # Check if user needs onboarding (default to completed=True if not explicitly set to False)
            if onboarding_completed == True or onboarding_completed is None:
                logger.info(f"User {user_id} has completed onboarding, skipping")
                return {"is_onboarding": False}
            
            if onboarding_completed == False:
                logger.info(f"User {user_id} needs onboarding, proceeding with conversational AI")
            
            # Use conversational AI to handle the onboarding
            ai_response = await self.generate_conversational_response(user_id, message, preferences)
            
            return {
                "is_onboarding": True,
                "completed": ai_response.get("completed", False),
                "message": ai_response.get("message", "Let me know what works best for you!")
            }
                
        except Exception as e:
            logger.error(f"Error processing onboarding message: {e}")
            return {"is_onboarding": False}
    
    async def start_onboarding(self, user_id: str, client_ip: str = None) -> Dict[str, Any]:
        """
        Start onboarding flow - returns messages to enqueue
        User will be asked to provide timezone manually during onboarding
        """
        try:
            # Clear default schedule preferences to ensure clean onboarding
            await self.clear_default_schedule_preferences(user_id)
            
            # Set fixed affirmation times (08:00, 12:00, 16:00)
            await self.set_default_affirmation_times(user_id)
            
            # Reset onboarding completion status and set initial step
            await self.supabase.set_preference_value(user_id, "onboarding_completed", False)
            await self.supabase.set_preference_value(user_id, "onboarding_step", OnboardingStep.START.value)
            
            # Generate conversational welcome
            welcome_message = self.get_welcome_message()
            first_message = await self.generate_initial_conversation()
            
            # Return messages array for Celery to send
            messages = []
            if welcome_message:
                messages.append(welcome_message)
            if first_message:
                messages.append(first_message)
                
            return {
                "messages": messages,
                "welcome_message": welcome_message,  # Keep for backwards compatibility
                "first_question": first_message    # Keep for backwards compatibility
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
    
    # ==================== CONVERSATIONAL AI ONBOARDING ====================
    
    async def generate_conversational_response(self, user_id: str, user_message: str, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Generate conversational AI response with reliable time extraction"""
        try:
            logger.debug(f"Conversational AI - Starting for user {user_id} with message: {user_message}")
            
            # Get conversation history for context
            conversation_history = self.build_conversation_context(preferences)
            logger.debug(f"Conversation context: {conversation_history}")
            
            # STEP 1: Try to extract time from user message directly
            extracted_time = await self.extract_time_from_message(user_message, preferences)
            logger.debug(f"Extracted time: {extracted_time}")
            
            if extracted_time:
                # STEP 2: Save the extracted time
                key, value = extracted_time
                
                # Handle timezone specially - store in current_timezone column
                if key == 'current_timezone':
                    await self.supabase.update_subscription(user_id, {
                        'current_timezone': value,
                        'timezone_updated_at': datetime.utcnow().isoformat()
                    })
                    logger.info(f"Saved timezone: {value}")
                    # CRITICAL: Update preferences dict so completion counting works correctly
                    preferences['current_timezone'] = value
                else:
                    await self.supabase.set_preference_value(user_id, key, value)
                    logger.info(f"Saved preference: {key} = {value}")
                    # Update preferences dict for completion counting
                    preferences[key] = value
                
                # STEP 3: Generate natural response acknowledging the time
                ai_response = await self.generate_natural_response(key, value, preferences, user_id)
                logger.debug(f"Natural response: {ai_response}")
                
                return {
                    "completed": ai_response.get("completed", False),
                    "message": ai_response.get("message", "Great! What's next?")
                }
            else:
                # No time found - generate a clarifying question
                clarifying_response = await self.generate_clarifying_response(user_message, preferences, user_id)
                return {
                    "completed": False,
                    "message": clarifying_response
                }
            
        except Exception as e:
            logger.error(f"Error in conversational AI processing: {e}")
            return {
                "completed": False,
                "message": "Tell me a bit about your daily routine - when do you usually start your day?"
            }
    
    async def extract_time_from_message(self, message: str, preferences: Dict[str, Any]) -> Optional[Tuple[str, str]]:
        """Extract time and determine which schedule key it belongs to with correction support"""
        try:
            # Check for explicit corrections first
            correction_key = self.detect_correction_intent(message)
            if correction_key:
                logger.info(f"Detected correction intent for: {correction_key}")
                if correction_key == 'weekly_reflection':
                    day, time = await self.parse_weekly_time(message)
                    if day and time:
                        return (correction_key, {"day": day, "time": time})
                else:
                    parsed_time = await self.parse_time(message, self.get_context_step_for_key(correction_key))
                    if parsed_time:
                        return (correction_key, parsed_time)
            
            # Check if we're in middle of onboarding - prioritize current step
            current_step = preferences.get('onboarding_step')
            if current_step and current_step != 'start':
                # Map step to preference key
                step_to_key = {
                    'day_planning': 'day_planning',
                    'accountability_checkin': 'accountability_checkin',
                    'evening_gratitude': 'evening_gratitude',
                    'weekly_reflection': 'weekly_reflection',
                    'timezone_location': 'current_timezone'
                }
                
                current_key = step_to_key.get(current_step)
                if current_key:
                    logger.info(f"Processing response for current step: {current_step}")
                    if current_key == 'weekly_reflection':
                        # Simplified - let LLM handle all weekly reflection parsing
                        day, time = await self.parse_weekly_time(message)
                        if day and time:
                            return (current_key, {"day": day, "time": time})
                    elif current_key == 'current_timezone':
                        # Handle timezone extraction using the natural language parser
                        timezone_detected = self.timezone_service.extract_timezone(message)
                        if timezone_detected:
                            return (current_key, timezone_detected)
                        else:
                            # If no valid timezone found, log and return None to trigger clarification
                            logger.warning(f"No valid timezone found in message: {message}")
                            return None
                    else:
                        parsed_time = await self.parse_time(message, self.get_context_step_for_key(current_key))
                        if parsed_time:
                            return (current_key, parsed_time)
            
            # Fallback to finding first missing item (original behavior)
            missing_items = [
                ('day_planning', 'planning'),
                ('accountability_checkin', 'progress'),
                ('evening_gratitude', 'bedtime'),
                ('weekly_reflection', 'weekly'),
                ('current_timezone', 'timezone')
            ]
            
            # Find the first missing item
            for key, label in missing_items:
                if not preferences.get(key):
                    if key == 'weekly_reflection':
                        day, time = await self.parse_weekly_time(message)
                        if day and time:
                            return (key, {"day": day, "time": time})
                    elif key == 'current_timezone':
                        # Handle timezone extraction using the natural language parser
                        timezone_detected = self.timezone_service.extract_timezone(message)
                        if timezone_detected:
                            return (key, timezone_detected)
                    else:
                        # Pass context for intelligent parsing
                        context_step = self.get_context_step_for_key(key)
                        parsed_time = await self.parse_time(message, context_step)
                        if parsed_time:
                            return (key, parsed_time)
                    break
            
            return None
        except Exception as e:
            logger.error(f"Error extracting time from message: {e}")
            return None
    
    def detect_correction_intent(self, message: str) -> Optional[str]:
        """Detect if user is trying to correct a previous time"""
        import re
        
        message_lower = message.lower()
        
        # Keywords that indicate correction intent
        correction_keywords = [
            'change', 'update', 'correct', 'fix', 'modify', 'adjust',
            'not', 'wrong', 'mistake', 'actually', 'instead',
            'mean', 'meant', 'should be', 'set to'
        ]
        
        has_correction_intent = any(keyword in message_lower for keyword in correction_keywords)
        
        if has_correction_intent:
            # Look for specific schedule mentions
            schedule_keywords = {
                'day_planning': ['planning', 'plan', 'day plan', 'schedule'],
                'accountability_checkin': ['progress', 'check in', 'checkin', 'accountability'],
                'evening_gratitude': ['bedtime', 'sleep', 'gratitude', 'bed'],
                'weekly_reflection': ['weekly', 'week', 'reflection', 'review']
            }
            
            for key, keywords in schedule_keywords.items():
                if any(keyword in message_lower for keyword in keywords):
                    return key
        
        return None
    
    async def clear_default_schedule_preferences(self, user_id: str):
        """Clear default schedule preferences to ensure clean onboarding (affirmation times are now fixed)"""
        try:
            schedule_keys = [
                'day_planning', 
                'accountability_checkin',
                'evening_gratitude',
                'weekly_reflection'
            ]
            
            for key in schedule_keys:
                await self.supabase.set_preference_value(user_id, key, None)
            
            logger.info(f"Cleared default schedule preferences for user {user_id}")
        except Exception as e:
            logger.error(f"Error clearing default preferences: {e}")
    
    def get_context_step_for_key(self, key: str) -> OnboardingStep:
        """Map preference key to OnboardingStep for context-aware parsing"""
        key_to_step = {
            'day_planning': OnboardingStep.DAY_PLANNING,
            'accountability_checkin': OnboardingStep.ACCOUNTABILITY_CHECKIN,
            'evening_gratitude': OnboardingStep.SLEEP_TIME,
            'weekly_reflection': OnboardingStep.WEEKLY_REFLECTION,
            'current_timezone': OnboardingStep.TIMEZONE_LOCATION
        }
        return key_to_step.get(key, OnboardingStep.START)
    
    async def generate_natural_response(self, key: str, value: str, preferences: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Generate natural response after successfully extracting time"""
        try:
            # Check if we have all required items (affirmation times are now fixed)
            all_items = ['day_planning', 'accountability_checkin', 'evening_gratitude', 'weekly_reflection', 'current_timezone']
            
            # Update preferences with new value (preferences dict now properly includes current_timezone from DB)
            preferences[key] = value
            
            # Count completed items
            completed_count = sum(1 for item in all_items if preferences.get(item))
            
            logger.debug(f"Completion check - {key}={value}, completed_count={completed_count}/5, preferences={preferences}")
            
            if completed_count >= 5:
                # Mark onboarding as completed in database immediately
                await self.supabase.mark_onboarding_completed(user_id)
                # Clear onboarding step since we're done
                await self.supabase.set_preference_value(user_id, "onboarding_step", None)
                logger.info(f"✅ Onboarding completed and persisted for user {user_id}")
                
                return {
                    "completed": True,
                    "message": self.get_completion_message()
                }
            
            # Update onboarding step for next question
            next_key = await self.get_next_missing_key(preferences)
            if next_key:
                # Map preference key to proper onboarding step
                key_to_step_mapping = {
                    'day_planning': OnboardingStep.DAY_PLANNING.value,
                    'accountability_checkin': OnboardingStep.ACCOUNTABILITY_CHECKIN.value,
                    'evening_gratitude': OnboardingStep.SLEEP_TIME.value,
                    'weekly_reflection': OnboardingStep.WEEKLY_REFLECTION.value,
                    'current_timezone': OnboardingStep.TIMEZONE_LOCATION.value
                }
                next_step = key_to_step_mapping.get(next_key, next_key)
                await self.supabase.set_preference_value(user_id, 'onboarding_step', next_step)
            
            # Generate next question
            next_question = await self.get_next_question(preferences)
            
            # Generate natural acknowledgment with AI
            formatted_time = self.format_time_ampm(value) if isinstance(value, str) else value
            acknowledgment = await self.generate_natural_acknowledgment(key, formatted_time, next_question)
            
            message = acknowledgment
            
            return {
                "completed": False,
                "message": message
            }
            
        except Exception as e:
            logger.error(f"Error generating natural response: {e}")
            return {
                "completed": False,
                "message": "What's your next preferred time?"
            }
    
    async def generate_clarifying_response(self, message: str, preferences: Dict[str, Any], user_id: str = None) -> str:
        """Generate natural clarifying question when no time is detected"""
        try:
            next_question = await self.get_next_question(preferences)
            
            # Let the LLM handle any clarification naturally through conversation
            # Remove rigid AM/PM detection - the AI can ask follow-up questions if needed
            
            # Generate natural clarification using AI
            prompt = f"""
            You're Maya, a warm AI life coach helping someone set up their daily routine.
            
            The user just responded with: "{message}"
            
            You couldn't detect a specific time in their message. You need to ask them again, but in a natural, friendly way.
            
            The next question you need to ask is: {next_question}
            
            TASK: Write a natural clarification that:
            1. Acknowledges their response warmly
            2. Gently asks for a specific time
            3. Shows understanding and patience
            
            STYLE GUIDELINES:
            - Sound conversational and friendly
            - Don't sound robotic or frustrated
            - Use varied expressions (I hear you, I understand, that makes sense, etc.)
            - Keep it under 40 words
            - Be encouraging and supportive
            
            Examples:
            "I hear you! Could you give me a specific time though? What time do you usually wake up?"
            "That makes sense! I just need a specific time - when do you prefer to plan your day?"
            "I understand! What specific time works best for your evening wind-down?"
            
            Write a natural clarification:
            """
            
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are Maya, a warm AI life coach. Generate natural, patient clarifications that feel human and understanding."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=80,
                temperature=0.7
            )
            
            clarification = response.choices[0].message.content.strip()
            clarification = clarification.replace('"', '').replace("'", "'")
            
            return clarification
            
        except Exception as e:
            logger.error(f"Error generating clarifying response: {e}")
            
            # Fallback to varied clarifications
            clarifications = [
                f"I hear you! Could you give me a specific time though? {next_question}",
                f"That makes sense! I just need a specific time - {next_question.lower()}",
                f"I understand! {next_question}",
                f"Got it! What specific time works best for you?",
                f"I see! Could you share a specific time? {next_question}"
            ]
            
            import random
            return random.choice(clarifications)
    
    async def get_next_question(self, preferences: Dict[str, Any]) -> str:
        """Get the next question to ask based on what's missing"""
        try:
            # Find the next missing preference
            questions_mapping = [
                ('day_planning', "When do you like to plan your day?"),
                ('accountability_checkin', "What time should I check in on your daily progress?"),
                ('evening_gratitude', "What time do you usually go to bed?"),
                ('weekly_reflection', "Which day and time would you like your weekly reflection?"),
                ('current_timezone', "What's your location or timezone so I can send messages at the right time for you?")
            ]
            
            for key, default_question in questions_mapping:
                if not preferences.get(key):
                    # For timezone, use a more direct approach to avoid AI confusion
                    if key == 'current_timezone':
                        return "Now, just to make sure I'm in sync with you, what time zone are you in?"
                    else:
                        # Try to generate a natural question for other keys
                        natural_question = await self.generate_natural_question(key, default_question)
                        return natural_question
            
            return "What other time preferences do you have?"
        except Exception as e:
            logger.error(f"Error getting next question: {e}")
            return "What time works best for you?"
    
    async def generate_natural_question(self, schedule_key: str, default_question: str) -> str:
        """Generate natural, varied questions instead of static ones"""
        try:
            # Activity descriptions for context
            activity_descriptions = {
                'day_planning': 'organize and plan your day',
                'accountability_checkin': 'check in on your daily progress',
                'evening_gratitude': 'practice gratitude before bed',
                'weekly_reflection': 'reflect on your week and plan ahead',
                'current_timezone': 'determine your timezone for perfectly timed messages'
            }
            
            activity = activity_descriptions.get(schedule_key, 'receive a message')
            
            prompt = f"""
            You're Maya, a warm AI life coach helping someone set up their daily routine.
            
            You need to ask when they'd like to {activity}.
            
            TASK: Write a natural, conversational question that:
            1. Sounds friendly and personal
            2. Explains briefly what this is for
            3. Asks for their preferred time
            
            STYLE GUIDELINES:
            - Sound like a supportive friend
            - Use varied expressions (don't always start with "What time...")
            - Keep it under 30 words
            - Be conversational and warm
            
            Examples:
            "When do you usually start your day? I'd love to send you morning motivation then!"
            "What time works best for planning your day? I'll help you organize your thoughts."
            "When do you like to wind down in the evening? I can send you relaxing messages then."
            
            Write a natural question about when to {activity}:
            """
            
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are Maya, a warm AI life coach. Generate natural, conversational questions that feel human and caring."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=60,
                temperature=0.7
            )
            
            question = response.choices[0].message.content.strip()
            question = question.replace('"', '').replace("'", "'")
            
            return question
            
        except Exception as e:
            logger.error(f"Error generating natural question: {e}")
            
            # Fallback to varied static questions
            question_variations = {
                'day_planning': [
                    "When do you like to plan your day?",
                    "What time works best for organizing your schedule?",
                    "When do you prefer to set your daily goals?",
                    "What time should I help you plan your day?"
                ],
                'accountability_checkin': [
                    "What time should I check in on your daily progress?",
                    "When would you like your daily accountability check?",
                    "What time works for reviewing your daily wins?",
                    "When should I ask about your progress?"
                ],
                'evening_gratitude': [
                    "What time do you usually go to bed?",
                    "When do you like to practice gratitude before sleep?",
                    "What time should I send your bedtime reflection?",
                    "When do you prefer your evening gratitude practice?"
                ],
                'weekly_reflection': [
                    "Which day and time would you like your weekly reflection?",
                    "When should we review your weekly progress?",
                    "What day and time works for your weekly check-in?",
                    "When would you like to reflect on your week?"
                ],
                'current_timezone': [
                    "What timezone are you in? (e.g. Africa/Casablanca or Europe/Amsterdam)",
                    "Which timezone should I use for your perfectly timed messages?",
                    "What's your current timezone? (like America/New_York or Europe/London)",
                    "Which timezone should I set for your location?"
                ]
            }
            
            import random
            variations = question_variations.get(schedule_key, [default_question])
            return random.choice(variations)
    
    async def get_next_missing_key(self, preferences: Dict[str, Any]) -> Optional[str]:
        """Get the next missing preference key"""
        all_keys = [
            'day_planning',
            'accountability_checkin',
            'evening_gratitude',
            'weekly_reflection',
            'current_timezone'
        ]
        
        for key in all_keys:
            if not preferences.get(key):
                return key
        
        return None
    
    async def generate_initial_conversation(self) -> str:
        """Generate the opening conversational message"""
        try:
            prompt = """
            You're Maya, a friendly AI life coach starting a conversation to learn about someone's daily schedule. 
            
            Generate a warm, natural opening message that:
            - Introduces yourself casually
            - Explains you want to learn their routine to send perfectly timed messages
            - Asks an open-ended question about their daily schedule
            - Feels conversational, not robotic
            - Is encouraging and personal
            
            Keep it under 50 words and make it feel like talking to a real person.
            """
            
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100,
                temperature=0.8
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating initial conversation: {e}")
            return "Hi! I'm Maya, your AI coach. I'd love to learn about your daily routine so I can send you perfectly timed motivation. What does a typical day look like for you?"
    
    def build_conversation_context(self, preferences: Dict[str, Any]) -> str:
        """Build context string of what we already know about the user"""
        context_parts = []
        missing_parts = []
        
        # Track what we have and what we need (only personalized preferences, not fixed affirmation times)
        schedule_items = [
            ('day_planning', 'Day planning'), 
            ('accountability_checkin', 'Progress check-in'),
            ('evening_gratitude', 'Bedtime/gratitude'),
            ('weekly_reflection', 'Weekly reflection'),
            ('current_timezone', 'Timezone')
        ]
        
        for key, label in schedule_items:
            value = preferences.get(key)
            if value and value != 'null' and value != '' and value is not None:
                if key == 'weekly_reflection' and isinstance(value, dict):
                    context_parts.append(f"✅ {label}: {value.get('day')} {value.get('time')}")
                else:
                    context_parts.append(f"✅ {label}: {value}")
            else:
                missing_parts.append(f"❓ {label}")
        
        # Check if we have any collected data OR if this is truly the first message
        onboarding_step = preferences.get('onboarding_step')
        if not context_parts and onboarding_step == 'start':
            return "FIRST CONVERSATION - No schedule collected yet. Start by introducing yourself as Maya and ask about wake-up time."
        
        context = "ONGOING CONVERSATION - Already collected:\n" + "\n".join(context_parts)
        if missing_parts:
            context += f"\n\nStill need:\n" + "\n".join(missing_parts)
            context += f"\n\nNEXT: Ask for the first missing item above. DON'T re-introduce yourself."
        
        return context
    
    def extract_preferences_from_response(self, ai_message: str) -> Dict[str, Any]:
        """Extract time preferences from AI response markers"""
        preferences = {}
        
        # Look for extraction markers - more flexible patterns
        extraction_patterns = [
            (r'\[EXTRACTED: day_planning: ([^\]]+)\]', 'day_planning'),
            (r'\[EXTRACTED: accountability_checkin: ([^\]]+)\]', 'accountability_checkin'),
            (r'\[EXTRACTED: evening_gratitude: ([^\]]+)\]', 'evening_gratitude'),
            (r'\[EXTRACTED: weekly_reflection: ([^\]]+)\]', 'weekly_reflection')
        ]
        
        for pattern, key in extraction_patterns:
            match = re.search(pattern, ai_message)
            if match:
                value = match.group(1).strip()
                
                # Handle weekly reflection specially
                if key == 'weekly_reflection':
                    parts = value.split()
                    if len(parts) >= 2:
                        preferences[key] = {
                            "day": parts[0].lower(),
                            "time": parts[1]
                        }
                else:
                    preferences[key] = value
        
        return preferences
    
    def clean_extraction_markers(self, message: str) -> str:
        """Remove extraction markers from AI message"""
        # Remove all extraction markers
        clean_message = re.sub(r'\[EXTRACTED: [^\]]+\]', '', message)
        clean_message = clean_message.replace('[ONBOARDING_COMPLETE]', '')
        
        # Clean up extra whitespace
        clean_message = re.sub(r'\n\s*\n', '\n\n', clean_message)
        return clean_message.strip()

    # ==================== PERSONALIZED QUESTION GENERATION ====================
    
    async def generate_personalized_question(self, step: OnboardingStep, user_preferences: Dict[str, Any]) -> str:
        """Generate personalized onboarding questions based on previous answers"""
        try:
            context = self.question_contexts.get(step)
            if not context:
                return "Please let me know when you'd like this scheduled."
            
            # Build context from previous answers - only include actual completed steps
            previous_answers = []
            preference_keys = ['day_planning', 'accountability_checkin', 'evening_gratitude', 'weekly_reflection']
            
            for key in preference_keys:
                value = user_preferences.get(key)
                if value and value != 'null' and value != '':  # Only include actual values
                    previous_answers.append(f"{key}: {value}")
            
            previous_context = "\n".join(previous_answers) if previous_answers else "This is the first question - no previous answers yet."
            
            question_prompts = {
                "day_planning": f"""Generate a warm, conversational question asking when the user wants to plan their day. 
                Keep it natural and friendly. Start with the emoji 📝 and make it feel like a personal coach asking.""",
                
                "progress_checkin": f"""The user plans their day at {user_preferences.get('day_planning', 'not specified yet')}. 
                Generate a question asking when they'd like a daily accountability check-in. Reference their planning time and suggest a logical time later in the day. 
                Start with 💪 and make it encouraging.""",
                
                "bedtime_gratitude": f"""The user has accountability check-ins at {user_preferences.get('accountability_checkin', 'not specified yet')}. 
                Generate a question asking about their bedtime for gratitude messages. Reference their daily schedule and suggest before sleep. 
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
                "day_planning": "📝 When would you like to plan your day?",
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
    
    def is_confirmation_response(self, user_input: str) -> bool:
        """Check if user is giving a confirmation response rather than a time"""
        confirmation_words = [
            "sure", "sounds good", "ok", "okay", "yes", "yeah", "yep", 
            "that works", "perfect", "good", "fine", "that's good", 
            "sounds great", "alright", "right"
        ]
        return user_input.lower().strip() in confirmation_words

    async def process_response(self, state: OnboardingStep, user_input: str) -> Tuple[bool, Any]:
        """
        Process user response for the current state using OpenAI for natural language understanding
        Returns: (is_valid, parsed_value)
        """        
        if state in [OnboardingStep.START, OnboardingStep.DAY_PLANNING,
                     OnboardingStep.ACCOUNTABILITY_CHECKIN, OnboardingStep.SLEEP_TIME]:
            
            # Handle confirmation responses - ask for clarification
            if self.is_confirmation_response(user_input):
                return False, "CONFIRMATION"
            
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
        """Parse time string using deterministic parser first, then OpenAI fallback"""
        try:
            # First try deterministic parsing
            deterministic_result = self.parse_time_deterministic(time_str, context_step)
            if deterministic_result:
                logger.info(f"✅ Deterministic parsing: '{time_str}' -> '{deterministic_result}'")
                return deterministic_result
            
            # Fall back to OpenAI parsing
            logger.info(f"⚠️ Falling back to OpenAI parsing for: '{time_str}'")
            return await self.parse_time_openai(time_str, context_step)
            
        except Exception as e:
            logger.error(f"Error parsing time: {e}")
            return None
    
    def parse_time_deterministic(self, time_str: str, context_step: OnboardingStep = None) -> Optional[str]:
        """Deterministic regex-based time parsing with sentence support"""
        import re
        
        # Normalize the input - remove common filler words and punctuation
        message = time_str.strip().lower()
        message = re.sub(r'\b(at|around|about|approximately|roughly|by|before|after|till|until)\b', '', message)
        message = re.sub(r'[^\w\s:.]', '', message)  # Remove punctuation except : and .
        message = re.sub(r'\s+', ' ', message).strip()  # Normalize whitespace
        
        # Pattern 1: "7am", "7 am", "7pm", "7 pm" - anywhere in sentence
        match = re.search(r'\b(\d{1,2})\s*(am|pm)\b', message)
        if match:
            hour = int(match.group(1))
            period = match.group(2)
            
            if period == 'am':
                if hour == 12:
                    hour = 0
            else:  # pm
                if hour != 12:
                    hour += 12
            
            return f"{hour:02d}:00"
        
        # Pattern 2: "7:30am", "7:30 pm" - anywhere in sentence
        match = re.search(r'\b(\d{1,2}):(\d{2})\s*(am|pm)\b', message)
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2))
            period = match.group(3)
            
            if period == 'am':
                if hour == 12:
                    hour = 0
            else:  # pm
                if hour != 12:
                    hour += 12
            
            return f"{hour:02d}:{minute:02d}"
        
        # Pattern 3: "7h30", "7.30" (additional formats)
        match = re.search(r'\b(\d{1,2})[h\.](\d{2})\b', message)
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2))
            
            # Use context for AM/PM determination
            if context_step in [OnboardingStep.ACCOUNTABILITY_CHECKIN, OnboardingStep.SLEEP_TIME]:
                if 1 <= hour <= 11:  # Assume PM for evening context
                    hour += 12
            
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                return f"{hour:02d}:{minute:02d}"
        
        # Pattern 4: "7:30", "13:30" (24-hour format) - anywhere in sentence
        match = re.search(r'\b(\d{1,2}):(\d{2})\b', message)
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2))
            
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                return f"{hour:02d}:{minute:02d}"
        
        # Pattern 5: Single number like "7", "13", "19" - anywhere in sentence
        match = re.search(r'\b(\d{1,2})\b', message)
        if match:
            hour = int(match.group(1))
            
            # If it's clearly 24-hour format (13-23), use as is
            if 13 <= hour <= 23:
                return f"{hour:02d}:00"
            
            # For ambiguous hours (1-12), use context
            if 1 <= hour <= 12:
                if context_step == OnboardingStep.DAY_PLANNING:
                    # Morning context - assume AM
                    return f"{hour:02d}:00"
                elif context_step in [OnboardingStep.ACCOUNTABILITY_CHECKIN, OnboardingStep.SLEEP_TIME]:
                    # Evening context - assume PM
                    if hour != 12:
                        hour += 12
                    return f"{hour:02d}:00"
            
            # Default to AM for ambiguous cases
            return f"{hour:02d}:00"
        
        # Special cases - anywhere in sentence
        if re.search(r'\b(noon|12pm|12 pm)\b', message):
            return "12:00"
        if re.search(r'\b(midnight|12am|12 am)\b', message):
            return "00:00"
        
        return None
    
    async def parse_time_openai(self, time_str: str, context_step: OnboardingStep = None) -> Optional[str]:
        """OpenAI-based time parsing as fallback"""
        try:
            # Build context for intelligent parsing
            context_info = ""
            if context_step:
                if context_step == OnboardingStep.SLEEP_TIME:
                    context_info = "This is for bedtime/sleep, so 11 likely means 11 PM (23:00)"
                elif context_step in [OnboardingStep.START, OnboardingStep.DAY_PLANNING]:
                    context_info = "This is for morning activities, so times are likely AM (8 = 08:00)"
                elif context_step == OnboardingStep.ACCOUNTABILITY_CHECKIN:
                    context_info = "This is for evening activities, so times are likely PM (7 = 19:00)"
            
            prompt = f"""
            Parse this user input into EXACT 24-hour time format (HH:MM).
            
            User input: "{time_str}"
            Context: {context_info}
            
            STRICT PARSING RULES:
            - "6pm" = "18:00" (NOT 20:00)
            - "6" (evening context) = "18:00" 
            - "11" (bedtime context) = "23:00"
            - "9 o'clock" = "09:00" (morning context)
            - "Sounds good" = INVALID (return "INVALID")
            - "Sure" = INVALID (return "INVALID")
            
            EXAMPLES:
            - "6pm" -> "18:00"
            - "6" (evening) -> "18:00"
            - "11" (bedtime) -> "23:00"
            - "9 o'clock" -> "09:00"
            - "Sounds good" -> "INVALID"
            - "Sure" -> "INVALID"
            
            Return ONLY the time in HH:MM format OR "INVALID" if not a time.
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
            
            # Handle invalid responses
            if result == "INVALID":
                return None
            
            # Validate the response format
            if result and re.match(r'^[0-2][0-9]:[0-5][0-9]$', result):
                return result
            
            logger.warning(f"Invalid time format returned: {result} for input: {time_str}")
            return None
        except Exception as e:
            logger.error(f"Error parsing time with OpenAI: {e}")
            return None
    
    async def generate_natural_acknowledgment(self, schedule_key: str, formatted_time: str, next_question: str) -> str:
        """Generate natural, conversational acknowledgment using AI"""
        try:
            # Map schedule keys to user-friendly activity descriptions
            activity_descriptions = {
                'day_planning': 'daily planning session',
                'accountability_checkin': 'daily progress check-in',
                'evening_gratitude': 'bedtime gratitude practice',
                'weekly_reflection': 'weekly reflection'
            }
            
            activity = activity_descriptions.get(schedule_key, 'scheduled message')
            
            # Create a natural acknowledgment prompt
            prompt = f"""
            You're Maya, a warm and encouraging AI life coach helping someone set up their daily routine. 
            
            The user just told you when they want their {activity} - at {formatted_time}.
            
            TASK: Write a natural, conversational acknowledgment that:
            1. Acknowledges their time choice warmly (vary your language - don't always say "Great!")
            2. Shows you understand what this means for their day
            3. Smoothly transitions to the next question
            
            STYLE GUIDELINES:
            - Sound like a supportive friend, not a robot
            - Use varied expressions (awesome, perfect, love it, sounds good, etc.)
            - Add a personal touch about how this fits their routine
            - Keep it under 50 words
            - Be conversational and natural
            
            Next question to ask: {next_question}
            
            Examples of natural acknowledgments:
            "Awesome! I'll send your morning motivation at 7:00 AM to help kickstart your day. What time do you usually plan your day?"
            "Perfect! A 1:00 PM energy boost sounds ideal for that afternoon slump. When do you prefer to wind down in the evening?"
            "Love it! Sunday at 11:00 AM is perfect for reflecting on your week."
            
            Write a natural acknowledgment for {activity} at {formatted_time}:
            """
            
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are Maya, a warm AI life coach. Generate natural, conversational acknowledgments that feel human and personal."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100,
                temperature=0.8  # Higher temperature for more natural variation
            )
            
            acknowledgment = response.choices[0].message.content.strip()
            
            # Clean up any formatting issues
            acknowledgment = acknowledgment.replace('"', '').replace("'", "'")
            
            return acknowledgment
            
        except Exception as e:
            logger.error(f"Error generating natural acknowledgment: {e}")
            
            # Fallback to varied static responses (better than single static response)
            fallback_acknowledgments = {
                'day_planning': [
                    f"Great choice! Daily planning at {formatted_time} will set you up for success.",
                    f"Perfect timing! I'll help you organize your day at {formatted_time}.",
                    f"Excellent! Planning at {formatted_time} will keep you on track."
                ],
                'accountability_checkin': [
                    f"Excellent! I'll check in on your progress at {formatted_time}.",
                    f"Perfect timing! Daily accountability at {formatted_time} will keep you motivated.",
                    f"Great! Your {formatted_time} check-in will help track your wins."
                ],
                'evening_gratitude': [
                    f"Perfect! Bedtime gratitude at {formatted_time} will end your day positively.",
                    f"Wonderful! I'll help you reflect at {formatted_time} before sleep.",
                    f"Great choice! Evening gratitude at {formatted_time} promotes better rest."
                ],
                'weekly_reflection': [
                    f"Perfect! Weekly reflection at {formatted_time} will help you grow.",
                    f"Excellent! I'll help you review your week at {formatted_time}.",
                    f"Great timing! Weekly check-in at {formatted_time} keeps you progressing."
                ],
                'current_timezone': [
                    f"Perfect! I've set your timezone to {formatted_time} for perfectly timed messages.",
                    f"Excellent! Now I can send messages at the right time in {formatted_time}.",
                    f"Great! Your timezone {formatted_time} is all set for optimal message timing."
                ]
            }
            
            import random
            fallback_options = fallback_acknowledgments.get(schedule_key, [f"Great! I'll send your message at {formatted_time}."])
            acknowledgment = random.choice(fallback_options)
            
            return f"{acknowledgment}\n\n{next_question}"
    
    def format_time_ampm(self, time_24h: str) -> str:
        """Convert 24-hour time to AM/PM format"""
        try:
            if not time_24h or ':' not in time_24h:
                return time_24h
            
            hour, minute = time_24h.split(':')
            hour = int(hour)
            
            if hour == 0:
                return f"12:{minute} AM"
            elif hour < 12:
                return f"{hour}:{minute} AM"
            elif hour == 12:
                return f"12:{minute} PM"
            else:
                return f"{hour-12}:{minute} PM"
        except:
            return time_24h
    
    async def parse_weekly_time(self, message: str) -> Tuple[Optional[str], Optional[str]]:
        """Parse weekly reflection day and time using OpenAI for natural language understanding"""
        try:
            prompt = f"""
            Parse user input to extract day and time for weekly reflection.
            
            User input: "{message}"
            
            PARSING EXAMPLES:
            - "Sunday at 10" -> {{"day": "sunday", "time": "10:00 AM"}}
            - "Sunday 11" -> {{"day": "sunday", "time": "11:00 AM"}}  
            - "Sunday 11 am" -> {{"day": "sunday", "time": "11:00 AM"}}
            - "Monday 9pm" -> {{"day": "monday", "time": "09:00 PM"}}
            - "Friday evening 7" -> {{"day": "friday", "time": "07:00 PM"}}
            
            RULES:
            - Use standard 12-hour format with AM/PM
            - If no AM/PM specified, assume AM for times 1-11, assume PM for evening context
            - Handle natural language flexibly
            - If user just says "AM" or "PM" alone, return null (incomplete)
            
            Valid days: monday, tuesday, wednesday, thursday, friday, saturday, sunday
            
            Return JSON: {{"day": "dayname", "time": "HH:MM AM/PM"}}
            If parsing fails: {{"day": null, "time": null}}
            
            Return ONLY the JSON object.
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
                    
                    # LLM should return time in "HH:MM AM/PM" format - just validate and store
                    if time_str and ('AM' in time_str.upper() or 'PM' in time_str.upper() or ':' in time_str):
                        return day, time_str
                    
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON response from OpenAI: {result}")
            
            return None, None
        except Exception as e:
            logger.error(f"Error parsing weekly time with OpenAI: {e}")
            return None, None
    
    # Note: parse_timezone method removed - now using TimezoneService.extract_timezone() 
    # which properly handles IANA timezone zones (e.g., 'America/New_York' instead of 'EST')
    
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
