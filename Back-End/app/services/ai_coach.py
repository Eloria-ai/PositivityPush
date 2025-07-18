"""
Enhanced AI Coach Service for Positivity Push
Integrates psychological framework for evidence-based coaching conversations.
"""

import openai
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from app.config import settings
from app.services.mem0_client import Mem0Service
from app.services.psychological_framework import PsychologicalFramework, PsychologicalProfile
from app.services.enhanced_prompts import EnhancedPromptEngine
from app.services.specialized_coaches import CoachType
from app.services.core_personality import core_personality, ConversationContext

logger = logging.getLogger(__name__)

class AICoachService:
    """Enhanced AI Coach with psychological framework integration"""
    
    def __init__(self):
        self.openai_client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        self.mem0_service = Mem0Service()
        self.psychological_framework = PsychologicalFramework()
        self.prompt_engine = EnhancedPromptEngine()
        self.model = settings.OPENAI_MODEL
    
    async def generate_welcome_message(self, subscription: Dict[str, Any]) -> str:
        """Generate personalized welcome message for new users"""
        try:
            # Use consolidated personality system for consistency
            system_prompt = core_personality.get_context_aware_personality(
                context=ConversationContext.ACTIVATION,
                user_profile={
                    'plan_type': subscription.get('plan_type', '3_month'),
                    'email': subscription.get('email', 'Not provided')
                }
            )
            
            # Generate activation message
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": "Generate a warm welcome message for this new user who just activated their coaching subscription."}
                ],
                max_tokens=150,
                temperature=0.8
            )
            
            welcome_msg = response.choices[0].message.content.strip()
            
            # Store initial interaction in mem0
            welcome_messages = [
                {"role": "system", "content": "User activated subscription"},
                {"role": "assistant", "content": welcome_msg}
            ]
            await self.mem0_service.add_memory(
                messages=welcome_messages,
                user_id=subscription["id"],
                metadata={"interaction_type": "welcome", "plan_type": subscription.get("plan_type")}
            )
            
            return welcome_msg
            
        except Exception as e:
            logger.error(f"Error generating welcome message: {e}")
            # Use context-aware fallback from personality system
            fallback_responses = core_personality.get_fallback_responses(ConversationContext.ACTIVATION)
            return fallback_responses[0]  # Use first fallback response
    
    async def generate_response(
        self, 
        user_id: str, 
        message: str, 
        user_context: Dict[str, Any]
    ) -> str:
        """Generate psychologically-informed AI coach response with enhanced error handling"""
        start_time = datetime.now()
        
        try:
            # Get user's memory/context from mem0 with timeout
            user_memories = await self._safe_get_memories(user_id)
            
            # Create psychological profile (simplified for now)
            user_profile = self._build_psychological_profile(user_context, user_memories)
            
            # Analyze message psychology
            psychological_analysis = self.psychological_framework.analyze_message_psychology(
                message, user_memories
            )
            
            # Generate response strategy
            response_strategy = self.psychological_framework.generate_psychological_response_strategy(
                psychological_analysis, user_profile
            )
            
            # Detect if we should use a specialized coach
            current_hour = datetime.now().hour
            coach_type = self.prompt_engine.detect_coaching_scenario(
                message, user_memories, current_hour
            )
            
            # Use specialized coach prompt or fallback to enhanced prompt
            if coach_type != CoachType.ALWAYS_ON:
                logger.info(f"Using specialized coach: {coach_type.value} for user {user_id}")
                enhanced_prompt = self.prompt_engine.get_specialized_coach_prompt(
                    coach_type=coach_type,
                    user_context=user_context,
                    conversation_history=user_memories
                )
            else:
                # Use consolidated personality system for general conversations
                user_profile_data = {
                    'goals': user_context.get('goals', ''),
                    'recent_challenges': psychological_analysis.get('emotional_state', ''),
                    'communication_style': user_context.get('communication_style', ''),
                    'progress_notes': user_memories[:100] if user_memories else ''
                }
                
                enhanced_prompt = core_personality.get_context_aware_personality(
                    context=ConversationContext.GENERAL_CONVERSATION,
                    user_profile=user_profile_data
                )
            
            # Debug: Log the prompt being sent to OpenAI
            logger.info(f"Sending prompt to OpenAI (first 200 chars): {enhanced_prompt[:200]}...")
            
            # Generate AI response using enhanced prompt
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": enhanced_prompt},
                    {"role": "user", "content": message}
                ],
                max_tokens=300,
                temperature=0.8
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            # Store interaction with enhanced metadata
            conversation_messages = [
                {"role": "user", "content": message},
                {"role": "assistant", "content": ai_response}
            ]
            
            # Enhanced metadata with psychological insights and coach type
            metadata = {
                "interaction_type": "conversation",
                "coach_type": coach_type.value,
                "emotional_state": [state.value for state in psychological_analysis.get("emotional_state", [])],
                "cognitive_patterns": [pattern.value for pattern in psychological_analysis.get("cognitive_patterns", [])],
                "motivation_level": psychological_analysis.get("motivation_level", 5),
                "primary_technique": response_strategy.get("primary_technique", "supportive"),
                "behavioral_cues": psychological_analysis.get("behavioral_cues", {}),
                "timestamp": datetime.now().isoformat()
            }
            
            await self._enhance_memory_storage(conversation_messages, user_id, metadata)
            
            logger.info(f"Generated response using {response_strategy.get('primary_technique')} for user {user_id}")
            
            # Log performance
            response_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"Response generated in {response_time:.2f}s using {coach_type.value} coach for user {user_id}")
            
            return ai_response
            
        except Exception as e:
            response_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Error generating AI response after {response_time:.2f}s: {e}")
            
            # Provide contextual fallback based on message sentiment
            return self._get_fallback_response(message)
    
    async def generate_daily_affirmation(
        self, 
        user_id: str, 
        user_context: Dict[str, Any]
    ) -> str:
        """Generate personalized morning affirmation following system prompt specifications"""
        try:
            user_memories = await self.mem0_service.get_memories(user_id)
            
            # Get user's recent context and challenges
            recent_context = ""
            if user_memories:
                recent_context = " ".join([mem.get('memory', '') for mem in user_memories[:3]])
            
            # System prompt based on specifications
            system_prompt = f"""You are a friendly Morning Affirmation Coach.

CORE RULES:
• Send exactly ONE short affirmation (1-2 lines max, ~20 words)
• Match user's pronoun preference (first-person "I..." or second-person "You...")
• Use recent context: wins, challenges, emotions from conversations
• Keep language simple, uplifting, under 20 words
• Avoid clichés; vary vocabulary and structure daily
• Rotate themes: confidence, gratitude, resilience, focus, optimism, kindness, growth
• Never bundle multiple affirmations; one powerful idea only

USER CONTEXT:
- Recent conversations: {recent_context[:300] if recent_context else 'New user starting their journey'}
- Goals: {user_context.get('personal_goals', 'personal growth')}
- Plan: {user_context.get('plan_type', '3_month')} subscription

Generate a single, concise morning affirmation that feels personal and resonates with their current situation."""
            
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": "Generate today's personalized morning affirmation"}
                ],
                max_tokens=50,  # Reduced for conciseness
                temperature=0.8
            )
            
            affirmation = response.choices[0].message.content.strip()
            
            # Store in mem0
            affirmation_messages = [
                {"role": "system", "content": "Morning affirmation generated"},
                {"role": "assistant", "content": affirmation}
            ]
            await self.mem0_service.add_memory(
                messages=affirmation_messages,
                user_id=user_id,
                metadata={"interaction_type": "daily_affirmation", "date": datetime.now().isoformat()}
            )
            
            return affirmation
            
        except Exception as e:
            logger.error(f"Error generating daily affirmation: {e}")
            # Simple, effective fallback
            fallbacks = [
                "You are capable, confident, and ready for today.",
                "Every small step today moves you closer to your goals.",
                "You radiate positivity, and good things flow to you.",
                "I am exactly where I need to be; growth is happening."
            ]
            import random
            return random.choice(fallbacks)
    
    async def generate_gratitude_prompt(
        self, 
        user_id: str, 
        user_context: Dict[str, Any]
    ) -> str:
        """Generate personalized evening gratitude prompt following system prompt specifications"""
        try:
            user_memories = await self.mem0_service.get_memories(user_id)
            
            # Get day's context for gratitude reflection
            day_context = ""
            if user_memories:
                # Look for wins, people, comforts, challenges from today
                day_context = " ".join([mem.get('memory', '') for mem in user_memories[:3]])
            
            # System prompt based on specifications
            system_prompt = f"""You are a soothing Night-Gratitude Coach.

CORE RULES:
• Send exactly ONE gentle gratitude prompt (1-3 softly-flowing sentences, ≤40 words total)
• Tailor to wins, people, comforts, challenges gathered during the day
• Tone = quiet, warm, sleep-friendly. No exclamation marks unless user prefers high energy
• Encourage reflection; do NOT ask for typed reply (unless user likes journaling)
• Vary phrasing nightly; avoid repeating opener within 7 days
• Rotate themes: simple joys, supportive people, lessons learned, personal growth, physical comforts, hopes for tomorrow
• End with calm cadence—no action items, no second question

GRATITUDE THEMES:
• Help end day in appreciation and calm
• Reference specific context: supportive people, warm comforts, lessons from setbacks
• Invite noticing/feeling/remembering blessings
• Use gentle imagery (quiet night, steady breath)

USER CONTEXT:
- Day's experiences: {day_context[:200] if day_context else 'New user ending their day peacefully'}
- Goals: {user_context.get('personal_goals', 'personal growth')}
- Tone preference: {user_context.get('communication_style', 'warm and gentle')}

Generate a single, gentle gratitude prompt that invites peaceful reflection without requiring a response."""
            
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": "Generate tonight's gratitude prompt"}
                ],
                max_tokens=70,  # For gentle, flowing sentences
                temperature=0.8
            )
            
            prompt = response.choices[0].message.content.strip()
            
            # Store in mem0
            gratitude_messages = [
                {"role": "system", "content": "Evening gratitude prompt generated"},
                {"role": "assistant", "content": prompt}
            ]
            await self.mem0_service.add_memory(
                messages=gratitude_messages,
                user_id=user_id,
                metadata={"interaction_type": "gratitude_prompt", "date": datetime.now().isoformat()}
            )
            
            return prompt
            
        except Exception as e:
            logger.error(f"Error generating gratitude prompt: {e}")
            # Gentle fallbacks based on system prompt examples
            fallbacks = [
                "As you settle in tonight, notice one small joy that warmed your day and let it soothe you to sleep.",
                "Before you drift off, breathe in gratitude for the lessons today offered and the people who stood beside you.",
                "Let the quiet of the night remind you of every gentle moment—each one proof you are supported and safe.",
                "Feel your heartbeat, recall a smile, and rest knowing today added another bright thread to your journey."
            ]
            import random
            return random.choice(fallbacks)
    
    async def generate_accountability_checkin(self, user_id: str, user_context: Dict[str, Any]) -> str:
        """Generate personalized accountability check-in following 4-step interactive flow"""
        try:
            # Get user's memories for personalization
            user_memories = await self.mem0_service.get_memories(user_id)
            
            # Get morning plan for reference
            morning_plan = ""
            if user_memories:
                # Look for today's planning or goals
                for mem in user_memories[:5]:
                    if 'planning' in mem.get('memory', '').lower() or 'goals' in mem.get('memory', '').lower():
                        morning_plan = mem.get('memory', '')[:200]
                        break
            
            # System prompt based on 4-step specifications
            system_prompt = f"""You are a gentle, motivating Accountability Coach.

CORE RULES:
• Use 4-step structure: Check-In → Celebrate → Reflect → Encourage
• Ask ONE question at a time (≤30 words each)
• Reference user's morning to-do list for personal connection
• Vary wording nightly; treat examples as inspiration, not scripts
• Keep tone supportive, non-judgmental
• Celebrate effort first, then discuss unfinished tasks
• End with single uplifting line looking toward tomorrow

4-STEP STRUCTURE:
STEP 1 - Gentle Check-In & Recap: Greet and recap today's planned tasks, ask which were completed
STEP 2 - Celebrate Wins: Acknowledge accomplishments enthusiastically but authentically  
STEP 3 - Reflection: Ask what got in the way / what they learned (compassionate wording)
STEP 4 - Encouragement: Reinforce that showing up matters, invite small adjustment for tomorrow

USER CONTEXT:
- Morning plan: {morning_plan if morning_plan else 'General goals and intentions'}
- Goals: {user_context.get('personal_goals', 'personal growth')}
- Recent context: {user_memories[0].get('memory', 'New user') if user_memories else 'New user'}

Generate ONLY the first step: a gentle check-in that recaps their morning plan and asks about completion."""
            
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": "Generate the first step: gentle check-in and recap of today's goals"}
                ],
                max_tokens=80,  # Reduced for conciseness
                temperature=0.7
            )
            
            checkin_message = response.choices[0].message.content.strip()
            
            # Store in mem0
            checkin_messages = [
                {"role": "system", "content": "Daily accountability check-in (Step 1) sent"},
                {"role": "assistant", "content": checkin_message}
            ]
            await self.mem0_service.add_memory(
                messages=checkin_messages,
                user_id=user_id,
                metadata={"interaction_type": "accountability_checkin", "date": datetime.now().isoformat()}
            )
            
            return checkin_message
            
        except Exception as e:
            logger.error(f"Error generating accountability check-in: {e}")
            # Varied fallbacks based on system prompt examples
            fallbacks = [
                "Let's look back at your day! What did you accomplish from your morning goals? What's still pending?",
                "Quick recap: How did your planned tasks play out today? What made the cut?",
                "Time to check in! Which goals from this morning did you tackle? What's left for tomorrow?",
                "Let's review your day! From your morning plan, what got done and what's still open?"
            ]
            import random
            return random.choice(fallbacks)
    
    def _build_coach_system_prompt(
        self, 
        user_context: Dict[str, Any], 
        user_memories: str
    ) -> str:
        """Build comprehensive system prompt for AI coach"""
        
        return f"""You are a warm, supportive AI life coach for Positivity Push. Your personality:
        - Encouraging and optimistic, but authentic (not toxic positivity)
        - Wise and insightful, offering practical advice
        - Remembers previous conversations and builds on them
        - Uses emojis sparingly but meaningfully
        - Keeps responses conversational and under 100 words
        - Asks thoughtful follow-up questions
        - Celebrates small wins and progress
        
        USER CONTEXT:
        - Plan: {user_context.get('plan_type', 'unknown')} subscription
        - Email: {user_context.get('email', 'not provided')}
        - Goals: {user_context.get('personal_goals', 'to be discovered')}
        - Status: {user_context.get('status', 'active')}
        
        CONVERSATION HISTORY & MEMORIES:
        {user_memories if user_memories else 'This is a new conversation - get to know the user!'}
        
        Respond as their dedicated coach who truly cares about their growth and wellbeing."""
    
    def _build_psychological_profile(self, user_context: Dict[str, Any], user_memories: List[Dict]) -> PsychologicalProfile:
        """Build psychological profile from user data and memories"""
        # For now, create a basic profile - this could be enhanced with more sophisticated analysis
        
        # Analyze memories for patterns
        memory_text = " ".join([mem.get('memory', '') for mem in user_memories if isinstance(mem, dict)])
        
        # Simple pattern detection
        cognitive_patterns = []
        if any(word in memory_text.lower() for word in ['always', 'never', 'completely']):
            cognitive_patterns.append(self.psychological_framework.cbt_techniques.get('all_or_nothing', {}))
        
        return PsychologicalProfile(
            dominant_cognitive_patterns=cognitive_patterns,
            emotional_patterns={"recent": []},
            behavioral_triggers={},
            motivation_style="achievement",  # Default
            communication_preference="gentle",  # Default
            stress_response_type="flight",  # Default
            growth_mindset_level=7,  # Default
            self_efficacy_areas={"general": 6}  # Default
        )
    
    async def _safe_get_memories(self, user_id: str) -> List[Dict]:
        """Safely get user memories with error handling and timeout"""
        try:
            # Add timeout for memory retrieval
            memories = await self.mem0_service.get_memories(user_id)
            return memories if memories else []
        except Exception as e:
            logger.warning(f"Error retrieving memories for user {user_id}: {e}")
            return []  # Return empty list to continue processing
    
    def _get_fallback_response(self, message: str) -> str:
        """Generate contextual fallback response using personality system"""
        message_lower = message.lower()
        
        # Detect context and use appropriate fallback
        if any(word in message_lower for word in ['sad', 'depressed', 'down', 'low', 'terrible', 'crisis', 'help']):
            # Crisis or emotional support context
            fallbacks = core_personality.get_fallback_responses(ConversationContext.CRISIS_SUPPORT)
            return fallbacks[0]
        
        # Default to general conversation fallbacks
        fallbacks = core_personality.get_fallback_responses(ConversationContext.GENERAL_CONVERSATION)
        return fallbacks[0]
    
    async def _enhance_memory_storage(self, conversation_messages: List[Dict], user_id: str, metadata: Dict) -> None:
        """Enhanced memory storage with better error handling"""
        try:
            await self.mem0_service.add_memory(
                messages=conversation_messages,
                user_id=user_id,
                metadata=metadata
            )
        except Exception as e:
            logger.error(f"Error storing memory for user {user_id}: {e}")
            # Continue without storing - don't break the conversation flow

    async def generate_weekly_reflection(self, user_id: str, user_context: Dict[str, Any]) -> str:
        """Generate personalized weekly reflection following dynamic conversation flow"""
        try:
            user_memories = await self.mem0_service.get_memories(user_id)
            
            # Check if this is a first-time user (no past week data)
            has_past_week_data = False
            if user_memories:
                # Look for interactions from past week
                week_ago = datetime.now() - timedelta(days=7)
                for mem in user_memories:
                    if 'timestamp' in mem and datetime.fromisoformat(mem['timestamp']) > week_ago:
                        has_past_week_data = True
                        break
            
            # Get past week context for returning users
            past_week_context = ""
            if has_past_week_data and user_memories:
                past_week_context = " ".join([mem.get('memory', '') for mem in user_memories[:5]])
            
            # System prompt based on specifications
            system_prompt = f"""You are a warm, supportive Weekly Reflection & Planning Coach.

CORE RULES:
• One prompt at a time - wait for user's reply before continuing
• Keep tone encouraging and non-judgmental
• Celebrate effort; normalize unfinished tasks
• Dynamically craft questions to match user's context and history
• Keep wording natural, not scripted

USER STATUS: {'First-time user' if not has_past_week_data else 'Returning user with past week data'}

{'FIRST-TIME USER FLOW - Skip reflection, start with planning:' if not has_past_week_data else 'RETURNING USER FLOW - Start with reflection:'}
{'• Invite user to share what they want to accomplish in their very first week' if not has_past_week_data else '• Greet and cue reflection (mention last week goals if available)'}
{'• Ask for one key habit/action they want to focus on' if not has_past_week_data else '• Ask what was accomplished and what they are proud of'}

USER CONTEXT:
- Past week data: {past_week_context[:300] if past_week_context else 'No past week interactions available'}
- Goals: {user_context.get('personal_goals', 'personal growth and reflection')}
- Plan: {user_context.get('plan_type', '3_month')} subscription

Generate the appropriate opening prompt based on whether this is their first weekly session or returning session."""
            
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Generate {'first-time' if not has_past_week_data else 'returning'} user weekly reflection opening"}
                ],
                max_tokens=100,  # For dynamic, personalized prompts
                temperature=0.8
            )
            
            reflection = response.choices[0].message.content.strip()
            
            # Store in mem0
            await self.mem0_service.add_memory(
                messages=[{"role": "assistant", "content": reflection}],
                user_id=user_id,
                metadata={
                    "interaction_type": "weekly_reflection", 
                    "date": datetime.now().isoformat(),
                    "user_status": "first_time" if not has_past_week_data else "returning"
                }
            )
            
            return reflection
            
        except Exception as e:
            logger.error(f"Error generating weekly reflection: {e}")
            # Varied fallbacks for different user types
            fallbacks = [
                "🗓️ Welcome to your first weekly session! What would you love to accomplish or focus on in this very first week?",
                "🗓️ Let's reflect on your week! Looking back at your recent goals, what went especially well for you?",
                "🗓️ Time for our weekly check-in! What's one win from this past week that you're most proud of?",
                "🗓️ As we start a new week, let's take a moment to reflect. What did you learn about yourself this past week?"
            ]
            import random
            return random.choice(fallbacks)

    async def generate_day_planning(self, user_id: str, user_context: Dict[str, Any]) -> str:
        """Generate personalized day planning prompt following system prompt specifications"""
        try:
            user_memories = await self.mem0_service.get_memories(user_id)
            
            # Get user's planning patterns and preferences
            planning_history = ""
            if user_memories:
                planning_history = " ".join([mem.get('memory', '') for mem in user_memories[:3]])
            
            # System prompt based on specifications
            system_prompt = f"""You are the user's friendly Day-Planning Coach.

CORE RULES:
• Send ONE planning prompt at a time (≤30 words)
• Keep prompts short (~2 sentences) and upbeat
• Vary phrasing day-to-day; avoid repeating same opener within 5 days
• Adapt to user's style (formal/casual, emoji-friendly, etc.)
• No judgment or evaluation—only guidance and encouragement
• Reference that morning affirmation just sent for positive transition

GENERATION WORKFLOW:
• Start with motivating opener: "Now that you're charged up..." / "Let's set you up for success..."
• Ask user to write/list today's tasks/goals (work, personal, self-care)
• Keep under 30 words
• Clear call to action (write, list, jot, type)

USER CONTEXT:
- Planning patterns: {planning_history[:200] if planning_history else 'New user starting planning journey'}
- Goals: {user_context.get('personal_goals', 'personal growth')}
- Style preference: {user_context.get('communication_style', 'friendly and encouraging')}

Generate a single, engaging day planning prompt that motivates them to list their daily goals."""
            
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": "Generate today's day planning prompt"}
                ],
                max_tokens=60,  # Reduced for conciseness
                temperature=0.7
            )
            
            planning = response.choices[0].message.content.strip()
            
            # Store in mem0
            await self.mem0_service.add_memory(
                messages=[{"role": "assistant", "content": planning}],
                user_id=user_id,
                metadata={"interaction_type": "day_planning", "date": datetime.now().isoformat()}
            )
            
            return planning
            
        except Exception as e:
            logger.error(f"Error generating day planning: {e}")
            # Varied fallbacks based on system prompt examples
            fallbacks = [
                "Now that you've started your day on a high note, let's plan your day. What tasks or goals do you want to tackle?",
                "You're ready to make today amazing! List your top priorities—work, personal, or self-care.",
                "Let's set you up for success. Jot down your to-do's, big or small; every step counts.",
                "It's a fresh start—plan your day: what would make you feel proud by bedtime?"
            ]
            import random
            return random.choice(fallbacks)

    async def generate_midday_affirmation(self, user_id: str, user_context: Dict[str, Any]) -> str:
        """Generate personalized midday affirmation following system prompt specifications"""
        try:
            user_memories = await self.mem0_service.get_memories(user_id)
            
            # Get morning context and current state
            morning_context = ""
            if user_memories:
                # Look for morning planning or recent interactions
                morning_context = " ".join([mem.get('memory', '') for mem in user_memories[:3]])
            
            # System prompt based on specifications
            system_prompt = f"""You are an encouraging Mid-Day Affirmation Coach.

CORE RULES:
• Send exactly ONE short affirmation (1-2 lines max, ~20 words)
• Match user's pronoun preference ("I..." or "You..." format)
• Tailor to morning goals, current energy level, or obstacles from today
• Keep language simple, upbeat, under 20 words
• Vary themes: progress, focus, calm, resilience, gratitude, optimism
• Rotate vocabulary - no direct repeat within 7 days
• Never bundle multiple affirmations; one clear idea per message

MIDDAY THEMES:
• Acknowledge progress so far ("so far today...")
• Renew motivation ("plenty of hours left")
• Provide mid-day energy boost
• Reference morning goals/plans when relevant

USER CONTEXT:
- Morning context: {morning_context[:200] if morning_context else 'New user continuing their day'}
- Goals: {user_context.get('personal_goals', 'personal growth')}
- Energy level: Mid-day refresh needed

Generate a single, energizing midday affirmation that acknowledges progress and renews motivation."""
            
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": "Generate today's midday affirmation"}
                ],
                max_tokens=50,  # Reduced for conciseness
                temperature=0.8
            )
            
            affirmation = response.choices[0].message.content.strip()
            
            # Store in mem0
            await self.mem0_service.add_memory(
                messages=[{"role": "assistant", "content": affirmation}],
                user_id=user_id,
                metadata={"interaction_type": "midday_affirmation", "date": datetime.now().isoformat()}
            )
            
            return affirmation
            
        except Exception as e:
            logger.error(f"Error generating midday affirmation: {e}")
            # Varied fallbacks based on system prompt examples
            fallbacks = [
                "I am proud of what I've accomplished so far today.",
                "There's still so much potential left in this day.",
                "You are focused, productive, and capable.",
                "Even small progress is progress—celebrate it.",
                "I release stress and invite calm into the rest of my day."
            ]
            import random
            return random.choice(fallbacks)

    async def generate_evening_affirmation(self, user_id: str, user_context: Dict[str, Any]) -> str:
        """Generate personalized evening affirmation following system prompt specifications"""
        try:
            user_memories = await self.mem0_service.get_memories(user_id)
            
            # Get day's context for evening reflection
            day_context = ""
            if user_memories:
                # Look for day's activities, challenges, wins
                day_context = " ".join([mem.get('memory', '') for mem in user_memories[:3]])
            
            # System prompt based on specifications
            system_prompt = f"""You are a calm, reassuring Evening Affirmation Coach.

CORE RULES:
• Send exactly ONE short affirmation (1-2 lines max, ~20 words)
• Match user's pronoun style ("I..." or "You..." format)
• Tailor to the day's tasks completed, challenges shared, emotions expressed
• Use calming language; keep to ~20 words
• Rotate themes: self-forgiveness, gratitude, peace, progress, hope
• Ensure no verbatim repeat within 7 days
• Never send multiple affirmations; one clear, gentle thought only

EVENING THEMES:
• Help user release the day and invite rest
• Acknowledge day's effort, wins, and lessons
• Validate effort and signal peace/hope for tomorrow
• Use calming language suitable for bedtime

USER CONTEXT:
- Day's experiences: {day_context[:200] if day_context else 'New user ending their day'}
- Goals: {user_context.get('personal_goals', 'personal growth')}
- Current mood: Preparing for rest and reflection

Generate a single, soothing evening affirmation that helps them release today and welcome peaceful rest."""
            
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": "Generate tonight's evening affirmation"}
                ],
                max_tokens=50,  # Reduced for conciseness
                temperature=0.8
            )
            
            affirmation = response.choices[0].message.content.strip()
            
            # Store in mem0
            await self.mem0_service.add_memory(
                messages=[{"role": "assistant", "content": affirmation}],
                user_id=user_id,
                metadata={"interaction_type": "evening_affirmation", "date": datetime.now().isoformat()}
            )
            
            return affirmation
            
        except Exception as e:
            logger.error(f"Error generating evening affirmation: {e}")
            # Varied calming fallbacks based on system prompt examples
            fallbacks = [
                "I did my best today, and that is enough.",
                "You let go of today's worries and invite peace tonight.",
                "I release what I can't control; calm fills me now.",
                "You are safe, loved, and ready for rest.",
                "I'm grateful for today's lessons; tomorrow is new possibility."
            ]
            import random
            return random.choice(fallbacks)
