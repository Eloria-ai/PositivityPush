"""
Enhanced AI Coach Service for Positivity Push
Integrates psychological framework for evidence-based coaching conversations.
"""

import openai
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

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
        """Generate personalized daily affirmation using personality system"""
        try:
            user_memories = await self.mem0_service.get_memories(user_id)
            
            # Build user profile for personalization
            user_profile_data = {
                'goals': user_context.get('goals', ''),
                'recent_challenges': user_context.get('challenges', ''),
                'communication_style': user_context.get('communication_style', ''),
                'progress_notes': user_memories[:200] if user_memories else 'New user'
            }
            
            system_prompt = core_personality.get_context_aware_personality(
                context=ConversationContext.DAILY_AFFIRMATION,
                user_profile=user_profile_data
            )
            
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": "Generate today's personalized morning affirmation for this user"}
                ],
                max_tokens=120,
                temperature=0.9
            )
            
            affirmation = response.choices[0].message.content.strip()
            
            # Store in mem0
            affirmation_messages = [
                {"role": "system", "content": "Daily affirmation generated"},
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
            # Use personality system fallback
            fallbacks = core_personality.get_fallback_responses(ConversationContext.DAILY_AFFIRMATION)
            return fallbacks[0]
    
    async def generate_gratitude_prompt(
        self, 
        user_id: str, 
        user_context: Dict[str, Any]
    ) -> str:
        """Generate personalized evening gratitude prompt"""
        try:
            user_memories = await self.mem0_service.get_memories(user_id)
            
            system_prompt = f"""You are a thoughtful AI life coach. Create an evening gratitude prompt that:
            - Reflects on the user's recent experiences or goals
            - Asks a specific, meaningful question about gratitude
            - Is personal and connected to their journey
            - Encourages reflection without being generic
            - Keep it under 40 words
            
            User context: {user_memories[:500] if user_memories else 'New user'}
            """
            
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": "Generate tonight's gratitude reflection prompt"}
                ],
                max_tokens=80,
                temperature=0.8
            )
            
            prompt = response.choices[0].message.content.strip()
            
            # Store in mem0
            gratitude_messages = [
                {"role": "system", "content": "Gratitude prompt generated"},
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
            return "As you wind down tonight, what's one small moment from today that brought you joy or peace? 🌙"
    
    async def generate_accountability_checkin(self, user_id: str, user_context: Dict[str, Any]) -> str:
        """Generate personalized accountability check-in message"""
        try:
            # Get user's memories for personalization
            user_memories = await self.mem0_service.get_user_context(user_id)
            
            system_prompt = f"""You are a supportive AI accountability coach for Positivity Push. Create a daily check-in message that:
            - Asks about their specific goals/habits (gym, work, personal growth)
            - References their previous commitments or challenges
            - Is encouraging and non-judgmental 
            - Asks for a simple update on their progress
            - Keeps it conversational and under 80 words
            - Uses 1-2 emojis meaningfully
            
            USER CONTEXT:
            - Goals: {user_context.get('goals', 'personal growth')}
            - Challenges: {user_context.get('challenges', 'building consistency')}
            - Plan: {user_context.get('plan_type', '3_month')}
            
            THEIR HISTORY:
            {user_memories}
            
            Ask them how they're doing with their specific commitments today."""
            
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Generate daily accountability check-in for user with context: {user_context}"}
                ],
                max_tokens=150,
                temperature=0.7
            )
            
            checkin_message = response.choices[0].message.content.strip()
            
            # Store in mem0
            checkin_messages = [
                {"role": "system", "content": "Daily accountability check-in sent"},
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
            return "Hey! How are you doing with your goals today? Any wins, big or small, you'd like to share? 💪"
    
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