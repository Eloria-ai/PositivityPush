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
        Process incoming webhook message during conversational onboarding
        Returns state change info for Celery task enqueuing
        """
        try:
            # Get current onboarding state
            preferences = await self.supabase.get_user_preferences(user_id)
            onboarding_completed = preferences.get("onboarding_completed", True)
            onboarding_step = preferences.get("onboarding_step")
            
            logger.info(f"Onboarding check for user {user_id}: completed={onboarding_completed}, step={onboarding_step}")
            
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
            
            # Generate conversational welcome
            welcome_message = self.get_welcome_message()
            first_message = await self.generate_initial_conversation()
            
            # Return messages for Celery to send
            return {
                "welcome_message": welcome_message,
                "first_question": first_message
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
        """Generate conversational AI response that naturally collects schedule preferences"""
        try:
            # Get conversation history for context
            conversation_history = self.build_conversation_context(preferences)
            
            # Create a smart system prompt that adapts based on what we know
            system_prompt = f"""
            You are Maya, a warm and intelligent AI life coach for Positivity Push. You're having a natural conversation to learn about the user's daily schedule so you can send perfectly timed motivational messages.

            CURRENT CONVERSATION CONTEXT:
            {conversation_history}

            YOUR MISSION:
            Through natural conversation, learn these 7 key times:
            1. Morning affirmation time (when they wake up/start their day)
            2. Day planning time (when they plan their daily tasks)  
            3. Midday motivation time (lunch/afternoon boost)
            4. Evening wind-down time (end of work day)
            5. Progress check-in time (evening reflection)
            6. Bedtime/gratitude time (before sleep)
            7. Weekly reflection time (day and time for weekly review)

            CONVERSATION STYLE:
            - Talk like a real person, not a rigid bot
            - Ask follow-up questions about their lifestyle and work
            - Show genuine curiosity about their routine
            - Extract times naturally through conversation
            - Reference what they've already shared
            - Be encouraging and supportive
            - Use natural transitions between topics

            SMART PARSING:
            When you get time information, store it in this format at the end of your response:
            [EXTRACTED: morning_affirmation: 07:00]
            [EXTRACTED: evening_affirmation: 18:00]
            [EXTRACTED: weekly_reflection: sunday 10:00]

            If you have all 7 times, end with: [ONBOARDING_COMPLETE]

            EXAMPLES OF NATURAL FLOW:
            "That's interesting! So you're up at 7 - do you jump right into work or do you have a morning routine? I'm thinking a quick motivation boost around then could be perfect..."

            "Since you mentioned lunch around 12:30, how's your energy in the afternoon? Some people love a little pick-me-up around 2 or 3..."

            Continue the conversation naturally based on what the user just said.
            """
            
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=300,
                temperature=0.8
            )
            
            ai_message = response.choices[0].message.content.strip()
            
            # Extract any preferences from the AI's response
            extracted_prefs = self.extract_preferences_from_response(ai_message)
            
            # Save extracted preferences
            for key, value in extracted_prefs.items():
                await self.supabase.set_preference_value(user_id, key, value)
            
            # Check if onboarding is complete
            if "[ONBOARDING_COMPLETE]" in ai_message:
                await self.supabase.mark_onboarding_completed(user_id)
                await self.supabase.set_preference_value(user_id, "onboarding_step", None)
                
                # Clean up the message
                clean_message = ai_message.replace("[ONBOARDING_COMPLETE]", "").strip()
                clean_message += "\n\n" + self.get_completion_message()
                
                return {
                    "completed": True,
                    "message": clean_message
                }
            
            # Clean up any extraction markers from the message
            clean_message = self.clean_extraction_markers(ai_message)
            
            return {
                "completed": False,
                "message": clean_message
            }
            
        except Exception as e:
            logger.error(f"Error generating conversational response: {e}")
            return {
                "completed": False,
                "message": "Tell me a bit about your daily routine - when do you usually start your day?"
            }
    
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
        
        if preferences.get('morning_affirmation'):
            context_parts.append(f"Morning time: {preferences['morning_affirmation']}")
        if preferences.get('day_planning'):
            context_parts.append(f"Planning time: {preferences['day_planning']}")
        if preferences.get('midday_affirmation'):
            context_parts.append(f"Midday time: {preferences['midday_affirmation']}")
        if preferences.get('evening_affirmation'):
            context_parts.append(f"Evening time: {preferences['evening_affirmation']}")
        if preferences.get('accountability_checkin'):
            context_parts.append(f"Check-in time: {preferences['accountability_checkin']}")
        if preferences.get('evening_gratitude'):
            context_parts.append(f"Bedtime: {preferences['evening_gratitude']}")
        if preferences.get('weekly_reflection'):
            weekly = preferences['weekly_reflection']
            if isinstance(weekly, dict):
                context_parts.append(f"Weekly: {weekly.get('day')} {weekly.get('time')}")
            else:
                context_parts.append(f"Weekly: {weekly}")
        
        if not context_parts:
            return "No schedule information collected yet - this is the beginning of the conversation."
        
        return "Already collected: " + ", ".join(context_parts)
    
    def extract_preferences_from_response(self, ai_message: str) -> Dict[str, Any]:
        """Extract time preferences from AI response markers"""
        preferences = {}
        
        # Look for extraction markers
        extraction_patterns = [
            r'\[EXTRACTED: morning_affirmation: ([^\]]+)\]',
            r'\[EXTRACTED: day_planning: ([^\]]+)\]',
            r'\[EXTRACTED: midday_affirmation: ([^\]]+)\]',
            r'\[EXTRACTED: evening_affirmation: ([^\]]+)\]',
            r'\[EXTRACTED: accountability_checkin: ([^\]]+)\]',
            r'\[EXTRACTED: evening_gratitude: ([^\]]+)\]',
            r'\[EXTRACTED: weekly_reflection: ([^\]]+)\]'
        ]
        
        for pattern in extraction_patterns:
            match = re.search(pattern, ai_message)
            if match:
                key = pattern.split(': ')[0].split('EXTRACTED: ')[1]
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
            preference_keys = ['morning_affirmation', 'day_planning', 'midday_affirmation', 'evening_affirmation', 'accountability_checkin', 'evening_gratitude']
            
            for key in preference_keys:
                value = user_preferences.get(key)
                if value and value != 'null' and value != '':  # Only include actual values
                    previous_answers.append(f"{key}: {value}")
            
            previous_context = "\n".join(previous_answers) if previous_answers else "This is the first question - no previous answers yet."
            
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
        if state in [OnboardingStep.START, OnboardingStep.MORNING_AFFIRMATION, OnboardingStep.DAY_PLANNING,
                     OnboardingStep.MIDDAY_AFFIRMATION, OnboardingStep.EVENING_AFFIRMATION,
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
    
    async def parse_weekly_time(self, message: str) -> Tuple[Optional[str], Optional[str]]:
        """Parse weekly reflection day and time using OpenAI for natural language understanding"""
        try:
            prompt = f"""
            Parse user input to extract day and time for weekly reflection.
            
            User input: "{message}"
            
            STRICT PARSING RULES:
            - "Sunday at 10" -> {{"day": "sunday", "time": "10:00"}}
            - "Sunday 11" -> {{"day": "sunday", "time": "11:00"}}
            - "Monday 9am" -> {{"day": "monday", "time": "09:00"}}
            - "Friday evening 7" -> {{"day": "friday", "time": "19:00"}}
            
            DEFAULT ASSUMPTIONS:
            - Weekly reflection times are typically morning (AM) unless specified
            - "10" means "10:00" (10 AM)
            - "11" means "11:00" (11 AM)
            
            Valid days: monday, tuesday, wednesday, thursday, friday, saturday, sunday
            
            Return JSON: {{"day": "dayname", "time": "HH:MM"}}
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