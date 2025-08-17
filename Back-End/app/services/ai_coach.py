"""
Enhanced AI Coach Service for Positivity Push
Integrates psychological framework for evidence-based coaching conversations.
"""

import openai
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from app.config import settings
from app.logging_config import get_logger
from app.services.mem0_client import Mem0Service
from app.services.psychological_framework import PsychologicalFramework, PsychologicalProfile
from app.services.enhanced_prompts import EnhancedPromptEngine
from app.services.specialized_coaches import CoachType
from app.services.core_personality import core_personality, ConversationContext
from app.services.pattern_tracker import PatternTracker

# Configure structured logging
logger = get_logger("app.services.ai_coach")

class AICoachService:
    """Enhanced AI Coach with psychological framework integration"""
    
    def __init__(self, supabase_service=None):
        self.openai_client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        self.mem0_service = Mem0Service()
        self.psychological_framework = PsychologicalFramework()
        self.prompt_engine = EnhancedPromptEngine()
        self.pattern_tracker = PatternTracker(supabase_service) if supabase_service else None
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
            logger.error("ai_welcome_message_error",
                        subscription_id=subscription.get("id"),
                        error=str(e),
                        exc_info=True)
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
                logger.info("ai_specialized_coach_selected",
                       user_id=user_id,
                       coach_type=coach_type.value)
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
            logger.debug("ai_prompt_debug",
                        user_id=user_id,
                        prompt_preview=enhanced_prompt[:200])
            
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
            
            logger.info("ai_response_generated",
                       user_id=user_id,
                       primary_technique=response_strategy.get('primary_technique'),
                       coach_type=coach_type.value)
            
            # Log performance
            response_time = (datetime.now() - start_time).total_seconds()
            logger.info("ai_response_performance",
                       user_id=user_id,
                       response_time_seconds=response_time,
                       coach_type=coach_type.value)
            
            return ai_response
            
        except Exception as e:
            response_time = (datetime.now() - start_time).total_seconds()
            logger.error("ai_response_error",
                        user_id=user_id,
                        response_time_seconds=response_time,
                        error=str(e),
                        exc_info=True)
            
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
            
            # Get anti-repetition instructions
            variety_addon = ""
            if self.pattern_tracker:
                variety_addon = await self.pattern_tracker.generate_anti_repetition_addon(user_id, 'daily_affirmation')
            
            # System prompt based on specifications with variety enforcement
            system_prompt = f"""You are a friendly Morning Affirmation Coach.

CORE RULES:
• Send exactly ONE short affirmation (15-22 words max)
• Must reference at least one concrete detail from recent conversations or user goals
• Match user's pronoun preference (first-person "I..." or second-person "You...")
• Use recent context: wins, challenges, emotions from conversations
• Keep language simple, uplifting
• Avoid clichés; vary vocabulary and structure daily
• Rotate themes: confidence, gratitude, resilience, focus, optimism, kindness, growth
• Never bundle multiple affirmations; one powerful idea only

USER CONTEXT:
- Recent conversations: {recent_context[:300] if recent_context else 'New user starting their journey'}
- Goals: {user_context.get('personal_goals', 'personal growth')}
- Plan: {user_context.get('plan_type', '3_month')} subscription{variety_addon}

Generate a single, concise morning affirmation that feels personal and resonates with their current situation."""
            
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": "Generate today's personalized morning affirmation"}
                ],
                max_tokens=50,  # Reduced for conciseness
                temperature=0.8,
                frequency_penalty=0.3,  # Reduce repetitive tokens
                presence_penalty=0.2    # Encourage topic diversity
            )
            
            affirmation = response.choices[0].message.content.strip()
            
            # Store pattern for future anti-repetition
            if self.pattern_tracker:
                await self.pattern_tracker.store_pattern(user_id, 'daily_affirmation', affirmation)
            
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
            logger.error("ai_daily_affirmation_error",
                        user_id=user_id,
                        error=str(e),
                        exc_info=True)
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
            
            # Get anti-repetition instructions
            variety_addon = ""
            if self.pattern_tracker:
                variety_addon = await self.pattern_tracker.generate_anti_repetition_addon(user_id, 'gratitude_prompt')
            
            # System prompt based on specifications with variety enforcement
            system_prompt = f"""You are a soothing Night-Gratitude Coach.

CORE RULES:
• Send exactly ONE gentle gratitude prompt (22-38 words max)
• Must reference at least one concrete detail from day's experiences or user context
• Include one concrete noticing cue (sound, sensation, a person)
• Tone = quiet, warm, sleep-friendly. No exclamation marks; one question max
• Vary opener from last 7 days; avoid repeating sentence structure
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
- Tone preference: {user_context.get('communication_style', 'warm and gentle')}{variety_addon}

Generate a single, gentle gratitude prompt that invites peaceful reflection without requiring a response."""
            
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": "Generate tonight's gratitude prompt"}
                ],
                max_tokens=70,  # For gentle, flowing sentences
                temperature=0.8,
                frequency_penalty=0.3,  # Reduce repetitive tokens
                presence_penalty=0.2    # Encourage topic diversity
            )
            
            prompt = response.choices[0].message.content.strip()
            
            # Store pattern for future anti-repetition
            if self.pattern_tracker:
                await self.pattern_tracker.store_pattern(user_id, 'gratitude_prompt', prompt)
            
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
            logger.error("ai_gratitude_prompt_error",
                        user_id=user_id,
                        error=str(e),
                        exc_info=True)
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
            logger.error("ai_accountability_checkin_error",
                        user_id=user_id,
                        error=str(e),
                        exc_info=True)
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
            logger.warning("ai_memory_retrieval_warning",
                          user_id=user_id,
                          error=str(e))
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
            logger.error("ai_memory_storage_error",
                        user_id=user_id,
                        error=str(e),
                        exc_info=True)
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
            
            # Get anti-repetition instructions
            variety_addon = ""
            if self.pattern_tracker:
                variety_addon = await self.pattern_tracker.generate_anti_repetition_addon(user_id, 'weekly_reflection')
            
            # Enhanced system prompt based on updated specifications
            if has_past_week_data:
                # Returning user - use structured weekly reflection format
                system_prompt = f"""You are a warm Weekly Reflection Coach.

STRUCTURE (80–120 words total):
1. Acknowledge their week with one concrete callback (win, challenge, person, or event) from memory
2. Ask one meaningful question about their progress or experiences (one question max)
3. Offer one insight or encouragement based on their journey  
4. Close with a forward-looking micro-step they can do in ≤2 minutes next week

CORE RULES:
• Warm and celebratory of progress made
• Honest about challenges without being negative
• Helps them see patterns and growth
• Natural, not scripted

USER CONTEXT:
- Week's conversations: {past_week_context[:300]}
- Goals: {user_context.get('personal_goals', 'personal growth')}
- Plan: {user_context.get('plan_type', '3_month')} subscription{variety_addon}

Create a reflection that helps them appreciate their journey and feel motivated for what's next."""
            else:
                # First-time user - planning focused
                system_prompt = f"""You are a warm Weekly Planning Coach for new users.

FIRST-TIME USER APPROACH:
• Since we're just getting started, focus on planning rather than reflection
• Invite them to share what they want to accomplish in their very first week
• Ask for one key habit or action they want to focus on
• Keep encouraging and forward-looking (80–120 words total)
• One question max

USER CONTEXT:
- Status: First weekly session
- Goals: {user_context.get('personal_goals', 'personal growth')}
- Plan: {user_context.get('plan_type', '3_month')} subscription{variety_addon}

Generate an encouraging first-week planning prompt that helps them set intentions."""
            
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Generate {'first-time' if not has_past_week_data else 'returning'} user weekly reflection opening"}
                ],
                max_tokens=150,  # For structured 80-120 word reflections
                temperature=0.8,
                frequency_penalty=0.3,  # Reduce repetitive tokens
                presence_penalty=0.2    # Encourage topic diversity
            )
            
            reflection = response.choices[0].message.content.strip()
            
            # Store pattern for future anti-repetition
            if self.pattern_tracker:
                await self.pattern_tracker.store_pattern(user_id, 'weekly_reflection', reflection)
            
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
            logger.error("ai_weekly_reflection_error",
                        user_id=user_id,
                        error=str(e),
                        exc_info=True)
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
            # Get anti-repetition instructions
            variety_addon = ""
            if self.pattern_tracker:
                variety_addon = await self.pattern_tracker.generate_anti_repetition_addon(user_id, 'day_planning')
            
            user_memories = await self.mem0_service.get_memories(user_id)
            
            # Get user's planning patterns and preferences
            planning_history = ""
            if user_memories:
                planning_history = " ".join([mem.get('memory', '') for mem in user_memories[:3]])
            
            # Enhanced system prompt with variety enforcement and concrete details
            system_prompt = f"""You are the user's friendly Day-Planning Coach.

CORE RULES:
• Send ONE planning prompt at a time (20-30 words max)
• Must reference at least one concrete detail from user context or planning history
• Keep prompts short (~2 sentences) and upbeat
• Vary phrasing day-to-day; avoid repeating same opener within 5 days
• Adapt to user's style (formal/casual, emoji-friendly, etc.)
• No judgment or evaluation—only guidance and encouragement
• Reference that morning affirmation just sent for positive transition

GENERATION WORKFLOW:
• Start with motivating opener: "Now that you're charged up..." / "Let's set you up for success..."
• Ask user to write/list today's tasks/goals (work, personal, self-care)
• Include concrete action verb: write, list, jot, type, organize
• Keep under 30 words total

USER CONTEXT:
- Planning patterns: {planning_history[:200] if planning_history else 'New user starting planning journey'}
- Goals: {user_context.get('personal_goals', 'personal growth')}
- Style preference: {user_context.get('communication_style', 'friendly and encouraging')}

Generate a single, engaging day planning prompt that motivates them to list their daily goals.{variety_addon}"""
            
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": "Generate today's day planning prompt"}
                ],
                max_tokens=60,  # Reduced for conciseness
                temperature=0.7,
                frequency_penalty=0.3,  # Reduce repetitive tokens
                presence_penalty=0.2    # Encourage topic diversity
            )
            
            planning = response.choices[0].message.content.strip()
            
            # Store pattern for future anti-repetition
            if self.pattern_tracker:
                await self.pattern_tracker.store_pattern(user_id, 'day_planning', planning)
            
            # Store in mem0
            await self.mem0_service.add_memory(
                messages=[{"role": "assistant", "content": planning}],
                user_id=user_id,
                metadata={"interaction_type": "day_planning", "date": datetime.now().isoformat()}
            )
            
            return planning
            
        except Exception as e:
            logger.error("ai_day_planning_error",
                        user_id=user_id,
                        error=str(e),
                        exc_info=True)
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
            
            # Get anti-repetition instructions
            variety_addon = ""
            if self.pattern_tracker:
                variety_addon = await self.pattern_tracker.generate_anti_repetition_addon(user_id, 'midday_affirmation')
            
            # System prompt based on specifications with variety enforcement
            system_prompt = f"""You are an encouraging Mid-Day Affirmation Coach.

CORE RULES:
• Send exactly ONE short affirmation (15-22 words max)
• Must reference at least one concrete detail from morning context or user goals
• Match user's pronoun preference ("I..." or "You..." format)
• Tailor to morning goals, current energy level, or obstacles from today
• Keep language simple, upbeat
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
- Energy level: Mid-day refresh needed{variety_addon}

Generate a single, energizing midday affirmation that acknowledges progress and renews motivation."""
            
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": "Generate today's midday affirmation"}
                ],
                max_tokens=50,  # Reduced for conciseness
                temperature=0.8,
                frequency_penalty=0.3,  # Reduce repetitive tokens
                presence_penalty=0.2    # Encourage topic diversity
            )
            
            affirmation = response.choices[0].message.content.strip()
            
            # Store pattern for future anti-repetition
            if self.pattern_tracker:
                await self.pattern_tracker.store_pattern(user_id, 'midday_affirmation', affirmation)
            
            # Store in mem0
            await self.mem0_service.add_memory(
                messages=[{"role": "assistant", "content": affirmation}],
                user_id=user_id,
                metadata={"interaction_type": "midday_affirmation", "date": datetime.now().isoformat()}
            )
            
            return affirmation
            
        except Exception as e:
            logger.error("ai_midday_affirmation_error",
                        user_id=user_id,
                        error=str(e),
                        exc_info=True)
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
            # Get anti-repetition instructions
            variety_addon = ""
            if self.pattern_tracker:
                variety_addon = await self.pattern_tracker.generate_anti_repetition_addon(user_id, 'evening_affirmation')
            
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

Generate a single, soothing evening affirmation that helps them release today and welcome peaceful rest.{variety_addon}"""
            
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": "Generate tonight's evening affirmation"}
                ],
                max_tokens=50,  # Reduced for conciseness
                temperature=0.8,
                frequency_penalty=0.3,  # Reduce repetition
                presence_penalty=0.2    # Encourage new content
            )
            
            affirmation = response.choices[0].message.content.strip()
            
            # Store pattern for anti-repetition
            if self.pattern_tracker:
                await self.pattern_tracker.store_pattern(user_id, 'evening_affirmation', affirmation)
            
            # Store in mem0
            await self.mem0_service.add_memory(
                messages=[{"role": "assistant", "content": affirmation}],
                user_id=user_id,
                metadata={"interaction_type": "evening_affirmation", "date": datetime.now().isoformat()}
            )
            
            return affirmation
            
        except Exception as e:
            logger.error("ai_evening_affirmation_error",
                        user_id=user_id,
                        error=str(e),
                        exc_info=True)
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
