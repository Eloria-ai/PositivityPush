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
        # ✅ FIX: Store the supabase_service properly
        self.supabase = supabase_service
    
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
                        error=str(e))
            # Use context-aware fallback from personality system
            fallback_responses = core_personality.get_fallback_responses(ConversationContext.ACTIVATION)
            return fallback_responses[0]  # Use first fallback response
    
    async def generate_response(
        self, 
        user_id: str, 
        message: str, 
        user_context: Dict[str, Any]
    ) -> str:
        """Generate natural, conversational AI coach response following human conversation patterns"""
        start_time = datetime.now()
        
        try:
            # Get user's memory/context from mem0 with timeout
            user_memories = await self._safe_get_memories(user_id)
            
            # Extract recent conversation context (last 3 interactions)
            recent_context = ""
            if user_memories:
                recent_context = " ".join([mem.get('memory', '') for mem in user_memories[:3]])
            
            # Get anti-repetition instructions for conversational responses
            variety_addon = ""
            if self.pattern_tracker:
                # Enable pattern tracking for conversational responses to prevent repetition
                variety_addon = await self.pattern_tracker.generate_anti_repetition_addon(user_id, 'conversation')
            
            # Build conversational system prompt with human conversation rules
            system_prompt = f"""You are Maya, a supportive friend and life coach. Have natural conversations that provide value, not interrogations.

HUMAN CONVERSATION RULES:
• ANSWER-FIRST: When asked a question, answer it directly before asking anything back
• QUESTION THROTTLE: Max one question every 2-3 turns; avoid back-to-back questions  
• ROTATE SPEECH ACTS: 40% reflect, 30% suggest, 20% inform, 10% ask
• MAKE IT CONCRETE: Anchor to specific details and show tiny examples when helpful

RESPONSE PATTERNS:
• REFLECT (40%): "I hear you saying..." + mirror their exact words
• SUGGEST (30%): "Here's one small thing to try..." + specific micro-step  
• INFORM (20%): "By that I mean..." + concrete explanation with example
• ASK (10%): "What's..." + one specific question (not "How do you feel?")

CONVERSATION FLOW:
• One idea per turn: one short sentence + one medium sentence
• Use contractions naturally, skip exclamation points unless they use them
• Tie to details from earlier when possible (names, tasks, times)
• Provide value through explanations and suggestions, not just questions

BANNED PATTERNS:
• Therapy language: "It sounds like you're feeling..." or "You might be experiencing..."
• Question stacking: Multiple questions in one response
• Vague responses: "Tell me more" without being specific about what
• Generic advice: Give concrete examples, not abstract concepts

DIRECT QUESTION RESPONSES:
• "What do you mean?" → Explain clearly with one concrete example
• "What are you talking about?" → "I mean [specific thing]. For example: [show it]"
• Confusion signals → Clarify immediately, don't ask what's confusing

USER CONTEXT:
- Recent conversations: {recent_context[:200] if recent_context else 'New conversation beginning'}
- Their goals: {user_context.get('personal_goals', 'exploring personal growth')}
- Communication style: {user_context.get('communication_style', 'casual and supportive')}{variety_addon}

Respond naturally by providing value first—explain, suggest, or reflect—before asking anything."""
            
            # Generate AI response with improved parameters for consistency
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                max_tokens=80,  # Reduced from 300 to enforce conciseness (≤60 words target)
                temperature=0.6,  # Reduced from 0.8 for more consistent adherence to rules
                frequency_penalty=0.4,  # Higher to prevent vocabulary repetition
                presence_penalty=0.3    # Higher to encourage fresh responses
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            # Comprehensive post-generation quality enforcement
            ai_response = self._enforce_post_generation_quality(ai_response, 'conversation', message)
            
            # Store pattern for anti-repetition (enable pattern tracking for conversations)
            if self.pattern_tracker:
                await self.pattern_tracker.store_pattern(user_id, 'conversation', ai_response)
            
            # Store interaction with simplified metadata  
            conversation_messages = [
                {"role": "user", "content": message},
                {"role": "assistant", "content": ai_response}
            ]
            
            # Simplified metadata focused on conversation quality
            metadata = {
                "interaction_type": "conversation",
                "response_length_words": len(ai_response.split()),
                "contains_question": "?" in ai_response,
                "timestamp": datetime.now().isoformat()
            }
            
            await self._enhance_memory_storage(conversation_messages, user_id, metadata)
            
            logger.info("ai_conversation_response_generated",
                       user_id=user_id,
                       response_length=len(ai_response.split()),
                       contains_question="?" in ai_response)
            
            # Log performance
            response_time = (datetime.now() - start_time).total_seconds()
            logger.info("ai_response_performance",
                       user_id=user_id,
                       response_time_seconds=response_time,
                       response_type="conversation")
            
            return ai_response
            
        except Exception as e:
            response_time = (datetime.now() - start_time).total_seconds()
            logger.error("ai_response_error",
                        user_id=user_id,
                        response_time_seconds=response_time,
                        error=str(e))
            
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
            
            # Extract user personalization preferences
            personalization = self._extract_user_personalization(user_context)
            
            # Humanized morning affirmation with authentic voice
            system_prompt = f"""You are a friendly Morning Affirmation Coach. Write with authentic, conversational warmth.

HUMAN AFFIRMATION RULES:
• One natural sentence (15-22 words, no questions or question marks)
• {personalization['pronoun_instruction']} with contractions when natural ("I'm", "You'll")
• Reference one specific, concrete detail from user's recent context
• Morning energy: forward-looking, gentle activation (not performative positivity)
• Natural conversational tone - avoid poetry, metaphors, or flowery language

AUTHENTIC VOICE PRINCIPLES:
• Use concrete nouns over abstract adjectives ("your call with Sarah" vs "your wonderful connection")
• One vivid detail beats three abstractions
• Prefer everyday phrasing over coaching-speak
• Match user's tone preference: {personalization['tone_preference']}
• Sound like a supportive friend, not a motivational poster

CONTENT VARIETY:
• Rotate themes naturally: confidence, gratitude, resilience, focus, optimism, kindness, growth, peace
• Vary sentence structure daily (not always declarative statements)
• Reference different aspects: recent wins, current challenges, upcoming goals, or personal growth
• Avoid same opener pattern for 5-7 days

BANNED ELEMENTS:
• Coaching clichés: joy, victories, momentum, journey, blessed, amazing, incredible
• Overly poetic language: magical, divine, sacred, radiant, luminous, magnificent  
• Generic motivation without personal context
• Questions, exclamations (unless user prefers exclamation marks)

USER CONTEXT:
- Recent conversations: {recent_context[:300] if recent_context else 'New user starting their journey'}
- Goals: {user_context.get('personal_goals', 'personal growth')}
- Communication style: {personalization['tone_preference']}
- Plan: {user_context.get('plan_type', '3_month')} subscription{variety_addon}

Generate a single, concise morning affirmation that feels personal and resonates with their current situation."""
            
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": "Generate today's personalized morning affirmation"}
                ],
                max_tokens=35,  # Aligned with 22-word target (1.6x safety margin)
                temperature=0.6,  # Lower for more consistent rule adherence
                frequency_penalty=0.4,  # Higher to prevent vocabulary repetition  
                presence_penalty=0.3    # Higher to encourage topic diversity
            )
            
            affirmation = response.choices[0].message.content.strip()
            
            # Comprehensive post-generation quality enforcement
            affirmation = self._enforce_post_generation_quality(affirmation, 'daily_affirmation')
            
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
                        error=str(e))
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
            
            # Night-Gratitude Style Card Implementation
            system_prompt = f"""You are a Night-Gratitude Coach following the exact Night-Gratitude Style Card specifications.

STYLE CARD REQUIREMENTS:
• Purpose: Gently cue appreciation; help user wind down
• Length: 22-38 words, 1-3 short sentences
• Questions: 0-1 (prefer none); if present, keep soft and single
• Tone: quiet, warm, sleep-friendly; NO exclamation marks
• Must include: one concrete noticing cue (sound/sensation/person/place/moment)
• Structure: 1) Soft cue to slow down 2) Concrete noticing prompt 3) Optional gentle closer

OPENER POOL (rotate daily):
"As you settle in", "Before you drift off", "In the quiet tonight", "With your next breath",
"As the day closes", "Let the stillness remind you", "When the house is quiet", "While you unwind"

CONCRETE NOTICING CUES:
• Sound/sensation/person/place/moment from today
• Reference real details when available (person, small win, comfort)
• Avoid abstract concepts - use specific, tangible elements

BANNED ELEMENTS:
• Hype/salesy language, directives to reply, stacked questions
• Clichés: "journey/joy/victories/momentum"
• Exclamation marks, energizing language

EXAMPLES TO MATCH:
"As you settle in, notice one small comfort from today—a kind word, warm light, or steady breath. Let that feeling linger."
"In the quiet tonight, recall a moment that eased your shoulders—someone's help, a laugh, or a calm step. Hold it for a few breaths."

USER CONTEXT:
- Day's experiences: {day_context[:100] if day_context else 'New user ending peacefully'}
- Goals: {user_context.get('personal_goals', 'personal growth')}
{variety_addon}

Generate 1-3 sentences (22-38 words) following the Night-Gratitude Style Card."""
            
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": "Generate tonight's gratitude prompt"}
                ],
                max_tokens=55,  # Aligned with 38-word target for natural flow
                temperature=0.6,  # Lower for consistent calm tone and rule adherence  
                frequency_penalty=0.4,  # Higher to prevent vocabulary repetition
                presence_penalty=0.3    # Higher for sensory variety
            )
            
            prompt = response.choices[0].message.content.strip()
            
            # Comprehensive post-generation quality enforcement  
            prompt = self._enforce_post_generation_quality(prompt, 'gratitude_prompt')
            
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
                        error=str(e))
            # Night-Gratitude Style Card compliant fallbacks
            fallbacks = [
                "As you settle in tonight, notice one small comfort from today—a kind word, warm light, or steady breath.",
                "Before you drift off, recall a moment that eased your shoulders—someone's help, a laugh, or calm step.",
                "In the quiet tonight, think of one person or small scene that made today softer.",
                "While you unwind, hold one gentle moment close—the warmth of coffee, a friend's voice, or quiet peace."
            ]
            import random
            return random.choice(fallbacks)
    
    async def generate_accountability_checkin(self, user_id: str, user_context: Dict[str, Any]) -> str:
        """Generate personalized accountability check-in following 4-step interactive flow"""
        try:
            # Get anti-repetition instructions
            variety_addon = ""
            if self.pattern_tracker:
                variety_addon = await self.pattern_tracker.generate_anti_repetition_addon(user_id, 'accountability_checkin')
            
            # Get user's memories for personalization
            user_memories = await self.mem0_service.get_memories(user_id)
            
            # Get today's actual daily plan with extracted goals from database
            today_date = datetime.now().strftime('%Y-%m-%d')
            daily_plan = await self.supabase.get_daily_plan_for_date(user_id, today_date)
            
            # Format planned items and goals for the prompt
            morning_plan_text = "General goals and intentions"
            goal_context = {}
            
            if daily_plan and daily_plan.get('items'):
                planned_items = daily_plan['items'][:5]  # Limit to 5 items for message length
                numbered_items = [f"{i+1}) {item}" for i, item in enumerate(planned_items)]
                morning_plan_text = "Your goals for today: " + ", ".join(numbered_items)
                
                # Include extracted goal analysis if available
                extracted_goals = daily_plan.get('extracted_goals', {})
                if extracted_goals:
                    goal_context = {
                        "categories": extracted_goals.get("categories", {}),
                        "insights": extracted_goals.get("insights", []),
                        "goal_count": len(extracted_goals.get("goals", []))
                    }
                    
            elif daily_plan and daily_plan.get('raw_text'):
                morning_plan_text = f"You planned: {daily_plan['raw_text'][:100]}"
            
            # Extract user personalization preferences
            personalization = self._extract_user_personalization(user_context)
            
            # Enhanced system prompt with personalization and anti-repetition
            system_prompt = f"""You are a gentle, motivating Accountability Coach.

CORE RULES - STEP 1 ONLY:
• Generate ONLY the first check-in step (≤30 words total)
• Ask exactly ONE question - no multiple questions or follow-ups
• Reference user's specific morning plan/tasks for personal connection
• {personalization['pronoun_instruction']}
• Tone: {personalization['tone_preference']} - supportive, non-judgmental
• Vary greeting/opener within 5-7 days - avoid same first 3 words
• End with single question about task completion

BANNED ELEMENTS:
• Multiple questions in same message
• Generic check-ins without morning plan reference  
• Words: amazing, incredible, fantastic, blessed, journey
• Follow-up questions or "Additionally" or "Also"

STRUCTURE REQUIREMENTS:
• Sentence 1: Warm greeting + morning plan recap
• Sentence 2: Single question about completion - if numbered items exist, ask "Which numbers are done? (e.g., 1,3)" otherwise ask "What did you finish?"

STEP 1 FOCUS:
Generate only a gentle check-in that recaps morning plan and asks which tasks were completed. No celebration, reflection, or encouragement - just the opening check-in.

USER CONTEXT:
- Morning plan: {morning_plan_text}  
- Goals: {user_context.get('personal_goals', 'personal growth')}
- Goal focus: {', '.join(goal_context.get('categories', {}).keys()) if goal_context.get('categories') else 'balanced planning'}
- Communication style: {personalization['tone_preference']}
- Recent context: {user_memories[0].get('memory', 'New user') if user_memories else 'New user'}{variety_addon}

Generate ONLY Step 1: gentle check-in with morning plan recap + single completion question."""
            
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": "Generate the first step: gentle check-in and recap of today's goals"}
                ],
                max_tokens=50,  # Aligned with 30-word target (1.6x safety margin)
                temperature=0.6,  # Lower for consistent rule adherence
                frequency_penalty=0.4,  # Higher to prevent vocabulary repetition
                presence_penalty=0.3    # Higher to encourage topic diversity
            )
            
            checkin_message = response.choices[0].message.content.strip()
            
            # Comprehensive post-generation quality enforcement
            checkin_message = self._enforce_post_generation_quality(checkin_message, 'accountability_checkin')
            
            # Store pattern for future anti-repetition
            if self.pattern_tracker:
                await self.pattern_tracker.store_pattern(user_id, 'accountability_checkin', checkin_message)
            
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
            
            # Set pending intent to capture user's completion response
            if daily_plan and daily_plan.get('items'):
                await self.supabase.set_pending_intent(user_id, 'capture_task_completion', today_date)
            
            return checkin_message
            
        except Exception as e:
            logger.error("ai_accountability_checkin_error",
                        user_id=user_id,
                        error=str(e))
            # Varied fallbacks based on system prompt examples
            fallbacks = [
                "How did today's goals go? Which ones did you finish?",
                "Quick check-in on your morning plan. What got done today?",
                "Time to see how your day went. Which tasks did you complete?",
                "Let's review your progress. What did you accomplish from your plan?"
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
    
    def _extract_user_personalization(self, user_context: Dict[str, Any]) -> Dict[str, str]:
        """Extract pronoun style and tone preferences from user context"""
        # Extract communication style and parse for pronoun preference
        comm_style = user_context.get('communication_style', 'warm and gentle')
        
        # Determine pronoun style from context or default to first-person
        pronoun_style = "first-person"  # Default: "I..." 
        if any(indicator in str(comm_style).lower() for indicator in ['you', 'direct', 'second']):
            pronoun_style = "second-person"  # "You..."
        
        # Map to clear prompt language
        pronoun_instruction = {
            'first-person': 'Use first-person format: "I am..." / "I will..." / "I can..."',
            'second-person': 'Use second-person format: "You are..." / "You will..." / "You can..."'
        }.get(pronoun_style, 'Use first-person format: "I am..." / "I will..." / "I can..."')
        
        # Extract tone preference
        tone_preference = comm_style if comm_style else "warm and encouraging"
        
        return {
            'pronoun_instruction': pronoun_instruction,
            'tone_preference': tone_preference,
            'pronoun_style': pronoun_style
        }
    
    def _enforce_word_limits(self, text: str, min_words: int, max_words: int, message_type: str = "") -> str:
        """Enforce word count limits on generated text"""
        if not text:
            return text
            
        words = text.strip().split()
        word_count = len(words)
        
        # If within limits, return as-is
        if min_words <= word_count <= max_words:
            return text
        
        # If too long, trim intelligently
        if word_count > max_words:
            # Try to cut at sentence boundary first
            sentences = text.split('.')
            if len(sentences) > 1:
                # Keep sentences until we're under limit
                result = ""
                for sentence in sentences:
                    potential = (result + sentence + ".").strip()
                    if len(potential.split()) <= max_words:
                        result = potential
                    else:
                        break
                if result:
                    logger.info(f"Word limit enforced for {message_type}: {word_count} → {len(result.split())} words (sentence boundary)")
                    return result
            
            # Fallback: hard truncate
            truncated = " ".join(words[:max_words])
            logger.info(f"Word limit enforced for {message_type}: {word_count} → {max_words} words (truncated)")
            return truncated
        
        # If too short, leave as-is (don't pad artificially)
        if word_count < min_words:
            logger.debug(f"Message under minimum for {message_type}: {word_count} words (min: {min_words})")
        
        return text
    
    def _enforce_post_generation_quality(self, ai_response: str, message_type: str, user_message: str = "") -> str:
        """Comprehensive post-generation quality enforcement for all message types"""
        if not ai_response:
            return ai_response
        
        original_response = ai_response
        response_lower = ai_response.lower()
        
        # 1. ENFORCE ONE QUESTION MAX - Remove extra questions
        question_count = ai_response.count('?')
        if question_count > 1:
            # Keep only the first question, remove others
            sentences = ai_response.split('.')
            kept_sentences = []
            questions_kept = 0
            
            for sentence in sentences:
                if '?' in sentence and questions_kept >= 1:
                    # Skip additional questions
                    continue
                elif '?' in sentence:
                    questions_kept += 1
                    kept_sentences.append(sentence)
                else:
                    kept_sentences.append(sentence)
            
            ai_response = '.'.join(kept_sentences).strip()
            if not ai_response.endswith('.') and not ai_response.endswith('?'):
                ai_response += '.'
            
            logger.info(f"Removed extra questions: {question_count} → 1 in {message_type}")
        
        # 2. GRATITUDE/EVENING TONE ENFORCEMENT - Strip exclamations, keep calm
        calm_message_types = ['gratitude_prompt', 'evening_affirmation']
        if message_type in calm_message_types:
            # Remove exclamation marks for calm tone
            ai_response = ai_response.replace('!', '.')
            # Fix double periods
            ai_response = ai_response.replace('..', '.')
            
            # Soften energetic language for evening
            evening_replacements = {
                'Let\'s': 'As you',
                'Time to': 'Take a moment to',
                'Ready to': 'Gently',
                'Get ready': 'Settle in to'
            }
            
            for energetic, calm in evening_replacements.items():
                ai_response = ai_response.replace(energetic, calm)
        
        # 3. THERAPY CLICHÉ BLOCKING
        therapy_phrases = {
            'i hear you saying': 'I see that you',
            'it sounds like you\'re feeling': 'it seems you\'re',
            'you might be feeling': 'you seem',
            'it sounds like you might be': 'it seems you\'re',
            'what i\'m hearing is': 'what I notice is',
            'i can hear that': 'I notice that',
            'that makes sense': 'I understand',
            'i can understand': 'I get that'
        }
        
        response_lower = ai_response.lower()
        for therapy_phrase, replacement in therapy_phrases.items():
            if therapy_phrase in response_lower:
                # Case-preserving replacement
                start_idx = response_lower.find(therapy_phrase)
                if start_idx != -1:
                    original_case = ai_response[start_idx:start_idx + len(therapy_phrase)]
                    if original_case[0].isupper():
                        replacement = replacement.capitalize()
                    ai_response = ai_response[:start_idx] + replacement + ai_response[start_idx + len(therapy_phrase):]
                    logger.info(f"Blocked therapy cliché '{therapy_phrase}' in {message_type}")
        
        # 4. PRONOUN HYGIENE - Bot never speaks as user
        pronoun_violations = [
            'i am ready to focus on my goals',
            'i will accomplish',
            'i can achieve',
            'my morning goals',
            'my daily plan'
        ]
        
        response_lower = ai_response.lower()
        for violation in pronoun_violations:
            if violation in response_lower:
                ai_response = ai_response.replace(violation, violation.replace('my ', 'your ').replace('i am', 'you are').replace('i will', 'you will').replace('i can', 'you can'))
                logger.info(f"Fixed pronoun violation '{violation}' in {message_type}")
        
        # 5. STYLE CARD COMPLIANCE - Message-specific checks
        style_card_checks = {
            'day_planning': {
                'word_range': (20, 30),
                'sentence_count': 2,
                'required_elements': ['action_verb'],
                'action_verbs': ['write', 'list', 'jot', 'type', 'plan', 'organize', 'note', 'outline'],
                'banned_words': ['amazing', 'crush it', 'incredible', 'fantastic'],
                'max_questions': 1,
                'no_exclamations': True
            },
            'gratitude_prompt': {
                'word_range': (22, 38),
                'sentence_count': (1, 3),
                'required_elements': ['concrete_noticing_cue'],
                'banned_words': ['journey', 'joy', 'victories', 'momentum', 'blessed', 'abundance'],
                'max_questions': 1,
                'prefer_questions': 0,
                'no_exclamations': True
            },
            'conversation': {'word_range': (0, 60), 'max_questions': 1},
            'daily_affirmation': {'word_range': (15, 22)},
            'accountability_checkin': {'word_range': (0, 35), 'max_questions': 1},
            'weekly_reflection': {'word_range': (80, 120)},
            'midday_affirmation': {'word_range': (15, 25)},
            'evening_affirmation': {'word_range': (15, 25), 'no_exclamations': True}
        }
        
        if message_type in style_card_checks:
            checks = style_card_checks[message_type]
            current_words = len(ai_response.split())
            
            # Word range enforcement
            if 'word_range' in checks:
                min_words, max_words = checks['word_range']
                if current_words > max_words and max_words > 0:
                    # Smart sentence-boundary trimming
                    sentences = ai_response.split('.')
                    kept_text = ""
                    
                    for sentence in sentences:
                        test_text = (kept_text + sentence + ".").strip()
                        if len(test_text.split()) <= max_words:
                            kept_text = test_text
                        else:
                            break
                    
                    if kept_text and kept_text != ai_response:
                        ai_response = kept_text
                        logger.info(f"Style card word limit enforced for {message_type}: {current_words} → {len(ai_response.split())} words")
            
            # Sentence count enforcement (for day_planning = exactly 2)
            if 'sentence_count' in checks:
                sentences = [s.strip() for s in ai_response.split('.') if s.strip()]
                required_count = checks['sentence_count']
                
                if isinstance(required_count, int) and len(sentences) != required_count:
                    if len(sentences) > required_count:
                        # Keep only the required number of sentences
                        ai_response = '. '.join(sentences[:required_count]) + '.'
                        logger.info(f"Sentence count enforced for {message_type}: {len(sentences)} → {required_count} sentences")
            
            # Action verb requirement (day_planning)
            if 'action_verbs' in checks:
                action_verbs = checks['action_verbs']
                response_lower = ai_response.lower()
                has_action_verb = any(verb in response_lower for verb in action_verbs)
                if not has_action_verb:
                    logger.warning(f"Missing action verb in {message_type}: {ai_response}")
            
            # Banned words enforcement
            if 'banned_words' in checks:
                banned_words = checks['banned_words']
                response_lower = ai_response.lower()
                for banned in banned_words:
                    if banned in response_lower:
                        # Simple replacement for common banned words
                        replacements = {
                            'amazing': 'good', 'incredible': 'great', 'fantastic': 'solid',
                            'crush it': 'do well', 'journey': 'path', 'victories': 'wins'
                        }
                        if banned in replacements:
                            ai_response = ai_response.replace(banned, replacements[banned])
                            logger.info(f"Replaced banned word '{banned}' in {message_type}")
            
            # No exclamations enforcement (gratitude, evening, day_planning)
            if checks.get('no_exclamations', False):
                if '!' in ai_response:
                    ai_response = ai_response.replace('!', '.')
                    ai_response = ai_response.replace('..', '.')
                    logger.info(f"Removed exclamations for calm tone in {message_type}")
        
        # 6. CONTEXTUAL FALLBACK for conversations that fail multiple checks
        if message_type == 'conversation' and user_message:
            validation_failures = []
            
            # Check if still has therapy language after cleaning
            remaining_therapy = any(phrase in ai_response.lower() for phrase in ['i hear you', 'it sounds like', 'you might be feeling'])
            if remaining_therapy:
                validation_failures.append('therapy_language')
                
            # Check if still over word limit significantly  
            if len(ai_response.split()) > 75:
                validation_failures.append('too_long')
                
            if validation_failures:
                # Generate simple contextual response based on user's message
                if any(word in user_message.lower() for word in ['what do you mean', 'what are you talking about', 'confused', "don't understand"]):
                    return "I mean making responses feel more natural and less scripted. What specific part would you like me to explain?"
                elif any(word in user_message.lower() for word in ['work', 'job', 'meeting', 'presentation']):
                    return "Work stress can build up quickly. What's the biggest challenge you're facing with it right now?"
                elif any(word in user_message.lower() for word in ['tired', 'exhausted', 'overwhelmed']):
                    return "That sounds draining. What's been taking up most of your energy lately?"
                elif any(word in user_message.lower() for word in ['excited', 'happy', 'good', 'great']):
                    return "That's good to hear. What's been going well for you?"
                else:
                    return "Tell me what's on your mind and I'll do my best to help."
        
        # Log if significant changes were made
        if ai_response != original_response:
            logger.info(f"Post-generation quality enforcement applied to {message_type}")
        
        return ai_response
    
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
                        error=str(e))
            # Continue without storing - don't break the conversation flow

    async def generate_weekly_reflection(self, user_id: str, user_context: Dict[str, Any]) -> str:
        """Generate personalized weekly reflection following dynamic conversation flow"""
        try:
            user_memories = await self.mem0_service.get_memories(user_id)
            
            # Get current week's aggregated goals from daily plans
            today = datetime.now()
            # Get Monday of current week (weekday() returns 0=Monday, 6=Sunday)
            monday_this_week = today - timedelta(days=today.weekday())
            week_start = monday_this_week.strftime('%Y-%m-%d')
            
            # Get or create weekly goals for this week
            weekly_goals = await self.supabase.get_weekly_goals(user_id, week_start)
            
            # Check if this is a first-time user (no past week data)
            has_past_week_data = False
            weekly_accomplishments = []
            
            if weekly_goals and weekly_goals.get('items'):
                has_past_week_data = True
                # Get completion data from daily plans for this week
                for day_offset in range(7):  # Monday to Sunday
                    day_date = monday_this_week + timedelta(days=day_offset)
                    day_str = day_date.strftime('%Y-%m-%d')
                    daily_plan = await self.supabase.get_daily_plan_for_date(user_id, day_str)
                    
                    if daily_plan and daily_plan.get('completion_status'):
                        completed_today = [status['item'] for status in daily_plan['completion_status'] if status.get('completed')]
                        weekly_accomplishments.extend(completed_today)
            elif user_memories:
                # Fallback to memory-based check for past week
                week_ago = datetime.now() - timedelta(days=7)
                for mem in user_memories:
                    if 'timestamp' in mem and datetime.fromisoformat(mem['timestamp']) > week_ago:
                        has_past_week_data = True
                        break
            
            # Format context for the prompt
            past_week_context = ""
            if has_past_week_data:
                if weekly_accomplishments:
                    past_week_context = f"Week's accomplishments: {', '.join(weekly_accomplishments[:10])}"
                elif user_memories:
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
- Weekly goals: {weekly_goals.get('items', []) if weekly_goals else 'No specific weekly goals set'}
- Accomplishments: {weekly_accomplishments[:5] if weekly_accomplishments else 'No tracked completions this week'}
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
            
            # Comprehensive post-generation quality enforcement
            reflection = self._enforce_post_generation_quality(reflection, 'weekly_reflection')
            
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
                        error=str(e))
            # Varied fallbacks for different user types
            fallbacks = [
                "Time for your first weekly check-in. What do you want to focus on this week?",
                "Let's look at how your week went. What went well for you?", 
                "Weekly reflection time. What's one thing you accomplished this week?",
                "Starting a new week - what did you learn about yourself recently?"
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
            
            # Note: Intentionally NOT using user_memories or planning_history
            # Each day should be treated fresh without assumptions from previous days
            
            # Day-Planning Style Card Implementation
            system_prompt = f"""You are a Day-Planning Coach following the exact Day-Planning Style Card specifications.

STYLE CARD REQUIREMENTS:
• Purpose: Ask user to outline today's tasks - NO assumptions about their work/projects
• Length: 20-30 words, two sentences exactly  
• Questions: exactly 1 question as the final sentence
• Tone: warm, plain, practical; NO exclamation marks
• Must include: one action verb (write/list/jot/type/plan/organize/note/outline)
• Structure: 1) Short orienting sentence 2) Simple question with action verb

CRITICAL RULES:
• DO NOT assume or state specific tasks, projects, or work ("app development", "presentations")
• DO NOT guess context from previous conversations
• ONLY invite them to share what they're planning - let THEM tell you
• Keep the question open-ended and task-neutral

OPENER POOL (rotate daily):
"Now that the morning's rolling", "Let's set you up for today", "Quick plan for today", 
"To make today smoother", "Before you dive in", "Let's give today some structure", 
"A simple start works best", "For a clear head"

EXAMPLES TO MATCH:
"Let's set you up for today. What would you like to accomplish?"
"Quick plan for today. What tasks are you focusing on?"
"Now that the morning's rolling. What's on your agenda today?"

USER CONTEXT:
- Today: Fresh new day with no assumptions about what they'll work on
- Goals: {user_context.get('personal_goals', 'general productivity')}
{variety_addon}

Generate exactly two sentences (20-30 words) following the Day-Planning Style Card."""
            
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": "Generate today's day planning prompt"}
                ],
                max_tokens=45,  # Aligned with 30-word target (1.5x safety margin)
                temperature=0.6,  # Lower for more consistent structure adherence
                frequency_penalty=0.4,  # Higher to prevent vocabulary repetition
                presence_penalty=0.3    # Higher to encourage topic diversity
            )
            
            planning = response.choices[0].message.content.strip()
            
            # Comprehensive post-generation quality enforcement
            planning = self._enforce_post_generation_quality(planning, 'day_planning')
            
            # Store pattern for future anti-repetition
            if self.pattern_tracker:
                await self.pattern_tracker.store_pattern(user_id, 'day_planning', planning)
            
            # Set pending intent to capture user's plan response
            today_date = datetime.now().strftime('%Y-%m-%d')
            await self.supabase.set_pending_intent(user_id, 'capture_day_plan', today_date)
            
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
                        error=str(e))
            # Varied fallbacks based on system prompt examples
            fallbacks = [
                "Let's set you up for today. Jot three priorities you'll feel good finishing.",
                "Quick plan for today. List the tasks that matter most to you.",
                "Before you dive in, give the day structure. Write your top three goals.",
                "To make today smoother, outline what needs your attention most."
            ]
            import random
            return random.choice(fallbacks)

    async def extract_goals_from_daily_plan(self, plan_items: List[str], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and categorize goals from daily plan items"""
        try:
            if not plan_items:
                return {"goals": [], "categories": {}, "recurring_patterns": []}
            
            # Prepare items for AI analysis
            items_text = "\n".join([f"{i+1}. {item}" for i, item in enumerate(plan_items)])
            
            system_prompt = f"""You are a goal analysis expert. Analyze the user's daily plan items to extract meaningful goals and patterns.

USER'S DAILY PLAN ITEMS:
{items_text}

ANALYSIS TASKS:
1. GOAL EXTRACTION: Identify the underlying goals/objectives behind each task
2. CATEGORIZATION: Classify goals into categories (health, work, personal, learning, social, etc.)
3. PATTERN RECOGNITION: Identify recurring vs one-time goals
4. GOAL REFINEMENT: Convert vague tasks into clear, actionable goals

RESPONSE FORMAT (JSON):
{{
    "goals": [
        {{
            "original_item": "go to gym",
            "extracted_goal": "maintain physical fitness", 
            "category": "health",
            "type": "recurring",
            "priority": "high"
        }}
    ],
    "categories": {{
        "health": 1,
        "work": 2,
        "personal": 1
    }},
    "insights": [
        "User focuses on health and work balance",
        "Strong commitment to family relationships"
    ]
}}

CATEGORIZATION GUIDELINES:
- health: fitness, exercise, medical, wellness, nutrition
- work: projects, meetings, deadlines, professional tasks
- personal: self-care, hobbies, organization, household
- social: family, friends, relationships, community
- learning: study, skills, reading, courses
- financial: budgeting, investments, purchases
- creative: art, writing, music, design

Return ONLY valid JSON."""

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Analyze these daily plan items: {items_text}"}
                ],
                max_tokens=800,
                temperature=0.3  # Lower temperature for consistent analysis
            )
            
            result = response.choices[0].message.content.strip()
            
            # Parse JSON response
            import json
            goal_analysis = json.loads(result)
            
            # Validate structure
            if not isinstance(goal_analysis.get("goals"), list):
                goal_analysis["goals"] = []
            if not isinstance(goal_analysis.get("categories"), dict):
                goal_analysis["categories"] = {}
            if not isinstance(goal_analysis.get("insights"), list):
                goal_analysis["insights"] = []
            
            return goal_analysis
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse goal analysis JSON: {e}")
            return {"goals": [], "categories": {}, "insights": []}
        except Exception as e:
            logger.error(f"Error extracting goals from daily plan: {e}")
            return {"goals": [], "categories": {}, "insights": []}

    async def generate_goal_acknowledgment(self, plan_items: List[str], goal_analysis: Dict[str, Any], user_context: Dict[str, Any]) -> str:
        """Generate a personalized acknowledgment of the user's daily goals"""
        try:
            if not plan_items:
                return "I'll check in with you later to see how your day goes!"
            
            # Prepare goal context for acknowledgment
            goals_summary = []
            categories = goal_analysis.get("categories", {})
            insights = goal_analysis.get("insights", [])
            
            # Create goal summary
            for i, item in enumerate(plan_items[:3]):  # Limit to top 3 for brevity
                goals_summary.append(f"{i+1}. {item.title()}")
            
            # Determine dominant category for personalized response
            dominant_category = max(categories.items(), key=lambda x: x[1])[0] if categories else "personal"
            
            system_prompt = f"""You are a supportive AI coach acknowledging the user's daily goals.

USER'S GOALS FOR TODAY:
{chr(10).join(goals_summary)}

GOAL ANALYSIS:
- Dominant focus: {dominant_category} 
- Goal insights: {', '.join(insights[:2]) if insights else 'balanced daily planning'}

ACKNOWLEDGMENT REQUIREMENTS:
• Length: 25-35 words, exactly 2 sentences
• Tone: supportive, encouraging, personal (but not overly enthusiastic)
• Structure: 1) Acknowledge their goals 2) Express confidence/support
• Include: reference to their goal focus ({dominant_category})
• NO exclamation marks, keep tone warm but measured

RESPONSE TEMPLATES TO VARY:
- "I've noted your [X] goals for today. I'll check in later to see how they went."
- "Your [X] focused plan looks solid. Looking forward to hearing how it unfolds."
- "Recorded your [X] priorities for today. I'll be curious about your progress later."

Generate a personalized acknowledgment following these guidelines."""

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Generate acknowledgment for these goals: {', '.join(plan_items)}"}
                ],
                max_tokens=150,
                temperature=0.7
            )
            
            acknowledgment = response.choices[0].message.content.strip()
            
            # Clean up formatting
            acknowledgment = acknowledgment.replace('"', '').replace("'", "'")
            
            return acknowledgment
            
        except Exception as e:
            logger.error(f"Error generating goal acknowledgment: {e}")
            # Fallback acknowledgments
            fallbacks = [
                f"I've noted your {len(plan_items)} goals for today. I'll check in later to see how they went.",
                f"Your plan looks solid with {len(plan_items)} priorities. Looking forward to hearing how it unfolds.",
                f"Recorded your goals for today. I'll be curious about your progress later."
            ]
            import random
            return random.choice(fallbacks)

    async def generate_goal_completion_response(self, user_id: str, daily_plan: Dict[str, Any], completed_items: List[int], raw_response: str, user_context: Dict[str, Any]) -> str:
        """Generate intelligent response to goal completion with follow-up questions for incomplete goals"""
        try:
            if not daily_plan or not daily_plan.get('items'):
                return "Thanks for the update! Keep up the great work."
            
            plan_items = daily_plan['items']
            extracted_goals = daily_plan.get('extracted_goals', {})
            goal_categories = extracted_goals.get('categories', {})
            goal_insights = extracted_goals.get('insights', [])
            
            # Analyze completion status
            total_goals = len(plan_items)
            completed_count = len(completed_items)
            completion_rate = completed_count / total_goals if total_goals > 0 else 0
            
            # Create completion analysis
            completed_goals = []
            incomplete_goals = []
            
            for i, goal in enumerate(plan_items):
                goal_number = i + 1
                if goal_number in completed_items:
                    completed_goals.append({"number": goal_number, "goal": goal})
                else:
                    incomplete_goals.append({"number": goal_number, "goal": goal})
            
            # Get user memories for personalization
            user_memories = await self.mem0_service.get_memories(user_id)
            memory_context = user_memories[0].get('memory', '') if user_memories else ''
            
            # Determine dominant incomplete category for targeted follow-up
            incomplete_categories = {}
            if incomplete_goals and extracted_goals.get('goals'):
                for extracted_goal in extracted_goals['goals']:
                    original_item = extracted_goal.get('original_item', '').lower()
                    category = extracted_goal.get('category', 'personal')
                    
                    # Check if this goal is incomplete
                    for incomplete in incomplete_goals:
                        if original_item in incomplete['goal'].lower() or incomplete['goal'].lower() in original_item:
                            incomplete_categories[category] = incomplete_categories.get(category, 0) + 1
                            break
            
            dominant_incomplete_category = max(incomplete_categories.items(), key=lambda x: x[1])[0] if incomplete_categories else None
            
            system_prompt = f"""You are a supportive AI coach responding to goal completion updates.

COMPLETION STATUS:
- Total goals: {total_goals}
- Completed: {completed_count} ({completion_rate:.0%})
- Completed goals: {[f"{g['number']}. {g['goal']}" for g in completed_goals]}
- Incomplete goals: {[f"{g['number']}. {g['goal']}" for g in incomplete_goals]}

GOAL ANALYSIS:
- Goal categories: {goal_categories}
- Main incomplete category: {dominant_incomplete_category or 'mixed'}
- Goal insights: {', '.join(goal_insights[:2]) if goal_insights else 'balanced planning'}

USER CONTEXT:
- Memory context: {memory_context[:100] if memory_context else 'New interaction'}
- Personal goals: {user_context.get('personal_goals', {})}

RESPONSE REQUIREMENTS:
• Length: 35-50 words total
• Structure: 1) Acknowledge completed goals positively 2) Ask ONE follow-up question about incomplete goals
• Tone: Supportive, curious, non-judgmental
• Focus: Understanding barriers, not blame

FOLLOW-UP QUESTION GUIDELINES:
- If {completion_rate:.0%} completion: {"Great job! What helped you stay on track?" if completion_rate >= 0.8 else "Nice progress! What got in the way of the others?" if completion_rate >= 0.5 else "What made some goals harder to tackle today?"}
- For {dominant_incomplete_category} goals: Include category-specific context
- Avoid: "What prevented you", "Why didn't you", blame-oriented language
- Use: "What got in the way", "What made it challenging", solution-oriented language

RESPONSE EXAMPLES:
- High completion: "Awesome work on [completed goals]! What helped you stay so focused today?"
- Mixed completion: "Great job on [completed goals]! What made [incomplete category] goals trickier today?"
- Low completion: "I see you tackled [completed goals]. What made the day more challenging than expected?"

Generate a supportive response with ONE thoughtful follow-up question."""

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"User completed goals: {completed_items} out of {list(range(1, total_goals + 1))}. Raw response: '{raw_response}'"}
                ],
                max_tokens=150,
                temperature=0.7
            )
            
            completion_response = response.choices[0].message.content.strip()
            
            # Clean up formatting
            completion_response = completion_response.replace('"', '').replace("'", "'")
            
            # Store insights in mem0 for future personalization
            insights = []
            if completion_rate >= 0.8:
                insights.append(f"User has high goal completion rate ({completion_rate:.0%})")
            elif completion_rate <= 0.3:
                insights.append(f"User struggles with goal completion ({completion_rate:.0%}) - may need simpler goals")
            
            if dominant_incomplete_category:
                insights.append(f"User tends to struggle with {dominant_incomplete_category} goals")
            
            if insights:
                await self.mem0_service.add_memory(
                    messages=[{"role": "system", "content": f"Goal completion insights: {', '.join(insights)}"}],
                    user_id=user_id,
                    metadata={"interaction_type": "goal_completion_analysis", "date": datetime.now().isoformat()}
                )
            
            return completion_response
            
        except Exception as e:
            logger.error(f"Error generating goal completion response: {e}")
            # Fallback responses based on completion rate
            if completed_items:
                return f"Nice work completing {len(completed_items)} goals! What made the other ones challenging today?"
            else:
                return "Thanks for the update! What made today's goals trickier than expected?"

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
            
            # Comprehensive post-generation quality enforcement
            affirmation = self._enforce_post_generation_quality(affirmation, 'midday_affirmation')
            
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
                        error=str(e))
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
            
            # Comprehensive post-generation quality enforcement  
            affirmation = self._enforce_post_generation_quality(affirmation, 'evening_affirmation')
            
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
                        error=str(e))
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

    # ===== ACCOUNTABILITY & DAILY PLAN TRACKING METHODS =====
    
    async def summarize_daily_plan(self, user_input: str, user_id: str) -> Dict[str, Any]:
        """Parse user's daily plan input and create structured summary with confirmation"""
        try:
            if not self.supabase:
                logger.warning("No supabase service available for plan summarization")
                return {
                    "items": [user_input],
                    "summary_message": f"Got it! Today you're planning: {user_input}\n\nI'll check back later to see how it went!"
                }

            # Enhanced system prompt for plan parsing
            system_prompt = """
You are an expert at parsing daily plans. Your task is to:

1. Extract 3-5 clear, actionable items from the user's daily plan
2. Structure them as specific, time-bound tasks when possible
3. Include timing if mentioned by the user
4. Make items concise but complete
5. Return JSON with the exact format below

Return JSON with this EXACT structure:
{
    "items": ["Specific actionable item 1", "Specific actionable item 2", "Specific actionable item 3"],
    "summary_message": "Great! So today you're planning to:\n\n1. Specific item with timing if mentioned\n2. Second specific item\n3. Third specific item\n\nI'll check back with you later to see how everything went. Have a productive day!"
}

Guidelines:
- Keep items specific and actionable
- Include time/location details if user mentions them
- Make items 1-2 sentences maximum
- Use encouraging, supportive tone
- Always include the follow-up promise
"""

            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Parse this daily plan: {user_input}"}
                ],
                max_tokens=400,
                temperature=0.3
            )
            
            try:
                parsed_plan = json.loads(response.choices[0].message.content)
                
                # Validate the response structure
                if not isinstance(parsed_plan.get("items"), list) or not parsed_plan.get("summary_message"):
                    raise ValueError("Invalid response structure")
                
                # Store in database using existing method
                today_date = datetime.now().strftime('%Y-%m-%d')
                success = await self.supabase.store_daily_plan(
                    user_id=user_id,
                    plan_date=today_date,
                    items=parsed_plan["items"],
                    raw_text=user_input
                )
                
                if success:
                    logger.info(f"Daily plan summarized and stored for user {user_id}: {len(parsed_plan['items'])} items")
                else:
                    logger.warning(f"Failed to store daily plan for user {user_id}")
                
                return parsed_plan
                
            except (json.JSONDecodeError, ValueError, KeyError) as e:
                logger.error(f"Failed to parse daily plan response: {e}")
                # Fallback to simple parsing
                return await self._fallback_plan_parsing(user_input, user_id)
                
        except Exception as e:
            logger.error(f"Error in summarize_daily_plan: {e}")
            return await self._fallback_plan_parsing(user_input, user_id)

    async def _fallback_plan_parsing(self, user_input: str, user_id: str) -> Dict[str, Any]:
        """Fallback plan parsing when AI fails"""
        try:
            # Use existing parsing method from SupabaseService
            items = self.supabase.parse_daily_plan_items(user_input) if self.supabase else [user_input]
            
            # Store in database
            today_date = datetime.now().strftime('%Y-%m-%d')
            if self.supabase:
                await self.supabase.store_daily_plan(
                    user_id=user_id,
                    plan_date=today_date,
                    items=items,
                    raw_text=user_input
                )
            
            # Create summary message
            if len(items) > 1:
                items_list = "\n".join([f"{i+1}. {item}" for i, item in enumerate(items)])
                summary_message = f"Great! So today you're planning to:\n\n{items_list}\n\nI'll check back with you later to see how everything went. Have a productive day!"
            else:
                summary_message = f"Got it! Today you're planning: {items[0]}\n\nI'll check back later to see how it went!"
            
            return {
                "items": items,
                "summary_message": summary_message
            }
            
        except Exception as e:
            logger.error(f"Error in fallback plan parsing: {e}")
            return {
                "items": [user_input],
                "summary_message": f"Got it! Today you're planning: {user_input}\n\nI'll check back later to see how it went!"
            }

    async def generate_accountability_checkin(self, user_id: str, date: str = None) -> str:
        """Generate accountability check-in message based on user's plans"""
        try:
            if not self.supabase:
                return "How did your day go? What went well and what was challenging?"
            
            if not date:
                date = datetime.now().strftime('%Y-%m-%d')
            
            # Get user's daily plan
            daily_plan = await self.supabase.get_daily_plan_for_date(user_id, date)
            
            if not daily_plan or not daily_plan.get('items'):
                return "How did your day go? What went well and what was challenging?"
            
            items = daily_plan['items']
            
            # Create personalized check-in message
            if len(items) == 1:
                return f"Hey! Earlier today you planned to: {items[0]}\n\nHow did it go? What went well and what was challenging?"
            else:
                items_list = "\n".join([f"{i+1}. {item}" for i, item in enumerate(items)])
                return f"Hey! Earlier today you planned to:\n\n{items_list}\n\nHow did it go? What went well and what was challenging?"
                
        except Exception as e:
            logger.error(f"Error generating accountability check-in: {e}")
            return "How did your day go? What went well and what was challenging?"

    async def process_accountability_response(self, user_id: str, response_text: str, date: str = None) -> str:
        """Process user's accountability check-in response and provide coaching"""
        try:
            if not date:
                date = datetime.now().strftime('%Y-%m-%d')
            
            # Get original plan for context
            daily_plan = await self.supabase.get_daily_plan_for_date(user_id, date) if self.supabase else None
            
            system_prompt = """
You are an encouraging AI accountability coach analyzing a user's daily reflection.

Your task:
1. Acknowledge what they shared positively
2. Celebrate any wins, no matter how small
3. Show understanding for challenges without judgment
4. Offer brief, actionable encouragement for tomorrow
5. Keep response warm but concise (2-3 sentences max)

Tone: Encouraging, understanding, forward-looking
Avoid: Being preachy, giving too much advice, dwelling on failures
"""

            # Build context string
            context_str = ""
            if daily_plan and daily_plan.get('items'):
                items_list = "\n".join([f"- {item}" for item in daily_plan['items']])
                context_str = f"User's original plan:\n{items_list}\n\n"
            
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"{context_str}User's reflection: {response_text}"}
                ],
                max_tokens=150,
                temperature=0.7
            )
            
            coaching_response = response.choices[0].message.content.strip()
            
            # Parse completion status and store (use existing method)
            if self.supabase and daily_plan:
                completed_items = self.supabase.parse_task_completion(response_text)
                if completed_items:
                    await self.supabase.update_task_completion(user_id, date, completed_items, response_text)
            
            # Store in conversation history
            if self.supabase:
                await self.supabase.log_conversation(
                    subscriber_id=user_id,
                    content=coaching_response,
                    message_type="assistant",
                    context_used={"interaction_type": "accountability_checkin", "date": date}
                )
            
            return coaching_response
            
        except Exception as e:
            logger.error(f"Error processing accountability response: {e}")
            return "Thanks for sharing how your day went! Every step forward is progress. Keep up the great work! 💪"

    async def generate_weekly_accountability_summary(self, user_id: str, week_start: str = None) -> str:
        """Generate weekly accountability summary based on week's plans and completions"""
        try:
            if not self.supabase:
                return "Hope you had a great week! Take some time to reflect on your wins and areas for growth."
            
            if not week_start:
                # Calculate current week start (Monday)
                today = datetime.now().date()
                week_start = (today - timedelta(days=today.weekday())).strftime('%Y-%m-%d')
            
            # Get week's accountability data using existing method
            weekly_data = await self.supabase.get_weekly_accountability_summary(user_id, week_start)
            
            plans = weekly_data.get('plans', [])
            checkins = weekly_data.get('checkins', [])
            
            if not plans:
                return "Hope you had a great week! Take some time to reflect on your wins and areas for growth."
            
            # Analyze the week's data
            total_planned = sum(len(plan.get('items', [])) for plan in plans)
            total_completed = 0
            
            for plan in plans:
                completion_status = plan.get('completion_status', [])
                if completion_status:
                    total_completed += sum(1 for item in completion_status if item.get('completed', False))
            
            completion_rate = int((total_completed / total_planned * 100)) if total_planned > 0 else 0
            
            # Generate summary using AI
            system_prompt = """
You are a supportive accountability coach creating a weekly summary.

Create an encouraging weekly reflection that:
1. Acknowledges the user's effort and planning
2. Celebrates their completion rate positively
3. Identifies patterns or insights (if any)
4. Encourages them for the upcoming week
5. Keeps it concise and motivating (3-4 sentences max)

Be genuine, encouraging, and forward-looking.
"""

            context = f"""
This week the user planned {total_planned} tasks across {len(plans)} days.
They completed {total_completed} tasks - that's {completion_rate}% completion rate.
Days with plans: {len(plans)}
Days with check-ins: {len(checkins)}
"""

            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Create a weekly summary based on: {context}"}
                ],
                max_tokens=200,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating weekly accountability summary: {e}")
            return "Hope you had a great week! Take some time to reflect on your wins and areas for growth."
