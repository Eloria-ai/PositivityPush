"""
AI Coach Service for Positivity Push
Powered by OpenAI GPT-4o mini with personalized coaching using mem0.
"""

import openai
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.config import settings
from app.services.mem0_client import Mem0Service

logger = logging.getLogger(__name__)

class AICoachService:
    """AI Coach powered by OpenAI GPT-4o mini with mem0 memory"""
    
    def __init__(self):
        self.openai_client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        self.mem0_service = Mem0Service()
        self.model = settings.OPENAI_MODEL
    
    async def generate_welcome_message(self, subscription: Dict[str, Any]) -> str:
        """Generate personalized welcome message for new users"""
        try:
            system_prompt = """You are a warm, enthusiastic AI life coach for Positivity Push. 
            A new user just activated their subscription. Create a welcoming message that:
            - Welcomes them warmly to Positivity Push
            - Explains you're their personal AI coach
            - Asks about their goals and what they'd like to work on
            - Sets a positive, encouraging tone
            - Keep it conversational and under 100 words
            """
            
            user_context = f"""
            User just completed payment for {subscription.get('plan_type', '3_month')} plan.
            Email: {subscription.get('email', 'Not provided')}
            """
            
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Generate welcome message for: {user_context}"}
                ],
                max_tokens=200,
                temperature=0.7
            )
            
            welcome_msg = response.choices[0].message.content.strip()
            
            # Store initial interaction in mem0
            await self.mem0_service.add_memory(
                user_id=subscription["id"],
                message=f"User just activated subscription. Sent welcome message: {welcome_msg}",
                metadata={"interaction_type": "welcome", "plan_type": subscription.get("plan_type")}
            )
            
            return welcome_msg
            
        except Exception as e:
            logger.error(f"Error generating welcome message: {e}")
            return """🎉 Welcome to Positivity Push! I'm your personal AI coach, here to support you on your journey to greater positivity and personal growth. 

I'm excited to get to know you! What are some goals you'd like to work on together? Whether it's building confidence, managing stress, or creating positive habits - I'm here to help! ✨"""
    
    async def generate_response(
        self, 
        user_id: str, 
        message: str, 
        user_context: Dict[str, Any]
    ) -> str:
        """Generate personalized AI coach response"""
        try:
            # Get user's memory/context from mem0
            user_memories = await self.mem0_service.get_memories(user_id)
            
            # Build context-aware system prompt
            system_prompt = self._build_coach_system_prompt(user_context, user_memories)
            
            # Create conversation messages
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ]
            
            # Generate AI response
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=300,
                temperature=0.8
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            # Store interaction in mem0
            await self.mem0_service.add_memory(
                user_id=user_id,
                message=f"User said: {message}. Coach responded: {ai_response}",
                metadata={"interaction_type": "conversation"}
            )
            
            return ai_response
            
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            return "I'm having a moment of reflection right now. Could you try again? I'm here to support you! 💭"
    
    async def generate_daily_affirmation(
        self, 
        user_id: str, 
        user_context: Dict[str, Any]
    ) -> str:
        """Generate personalized daily affirmation"""
        try:
            user_memories = await self.mem0_service.get_memories(user_id)
            
            system_prompt = f"""You are a personalized AI life coach. Create a daily affirmation that:
            - Is specific to this user's goals and challenges
            - Uses their name if available: {user_context.get('email', '').split('@')[0] if user_context.get('email') else 'friend'}
            - Is empowering and actionable
            - References their recent conversations or progress
            - Keep it under 50 words
            - Start with a warm greeting like "Good morning" or "Today"
            
            User memories: {user_memories[:500] if user_memories else 'New user, no previous context'}
            """
            
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": "Generate today's personalized affirmation"}
                ],
                max_tokens=100,
                temperature=0.9
            )
            
            affirmation = response.choices[0].message.content.strip()
            
            # Store in mem0
            await self.mem0_service.add_memory(
                user_id=user_id,
                message=f"Sent daily affirmation: {affirmation}",
                metadata={"interaction_type": "daily_affirmation", "date": datetime.now().isoformat()}
            )
            
            return affirmation
            
        except Exception as e:
            logger.error(f"Error generating daily affirmation: {e}")
            return "Today is a new opportunity to grow, learn, and spread positivity. You've got this! ✨"
    
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
            await self.mem0_service.add_memory(
                user_id=user_id,
                message=f"Sent gratitude prompt: {prompt}",
                metadata={"interaction_type": "gratitude_prompt", "date": datetime.now().isoformat()}
            )
            
            return prompt
            
        except Exception as e:
            logger.error(f"Error generating gratitude prompt: {e}")
            return "As you wind down tonight, what's one small moment from today that brought you joy or peace? 🌙"
    
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