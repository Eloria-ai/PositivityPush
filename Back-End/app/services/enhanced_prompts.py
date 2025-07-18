"""
Enhanced AI Coach Prompts with Psychological Framework
Evidence-based prompt engineering for therapeutic effectiveness
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from app.services.psychological_framework import PsychologicalFramework, PsychologicalProfile
from app.services.specialized_coaches import SpecializedCoaches, CoachType, CoachingContext

class EnhancedPromptEngine:
    """Advanced prompt engineering with psychological principles"""
    
    def __init__(self):
        self.framework = PsychologicalFramework()
        self.specialized_coaches = SpecializedCoaches()
        self.base_personality = self._create_base_personality()
        self.therapeutic_techniques = self._load_therapeutic_techniques()
        
    def _create_base_personality(self) -> str:
        """AI mindset coach inspired by Wysa, Woebot, and Youper"""
        return """You are **Positivity Push**, an AI mindset coach for WhatsApp inspired by top apps Wysa, Woebot, and Youper.

GOALS  
• Sound like a thoughtful human, not a script.  
• Offer empathy first, insight second, tiny action last.  
• Keep replies under ~90 words; shorter is fine.  
• End with a natural encouragement or light emoji (not every time).

BEST-PRACTICE FLOW  (flexible—skip / reorder if it feels robotic)  
1. Brief emotional validation (≤ 15 words).  
2. One curious follow-up or reframe that invites reflection.  
3. Suggest a micro-step that can be done in ≤ 2 minutes.  
4. Close with genuine support (emoji optional).

STYLE  
• Warm, conversational, non-clinical.  
• Vary phrasing; avoid repeating the same opener twice in a row.  
• Use contractions ("I'm", "you'll").  
• One question max per message.  
• No numbered lists."""

    def _load_therapeutic_techniques(self) -> Dict[str, Dict]:
        """Therapeutic response templates"""
        return {
            "emotional_validation": {
                "overwhelmed": [
                    "That feeling of being overwhelmed makes complete sense given everything you're juggling.",
                    "When we're overwhelmed, our brain's threat detection system is on high alert - it's actually trying to protect you."
                ],
                "frustrated": [
                    "I can hear the frustration in your words, and that's completely valid.",
                    "Frustration often signals that something important to you isn't working as expected."
                ],
                "anxious": [
                    "Anxiety is your mind's way of trying to prepare for challenges - it shows you care deeply.",
                    "That anxious energy you're feeling? It's actually your system trying to keep you safe."
                ]
            },
            "cognitive_restructuring": {
                "all_or_nothing": [
                    "I notice some 'all-or-nothing' thinking there. What might be true in the middle ground?",
                    "When you say 'always' or 'never' - what are some exceptions to that pattern?"
                ],
                "catastrophizing": [
                    "What evidence do you have that this worst-case scenario will happen?",
                    "If your best friend shared this worry, what would you tell them?"
                ],
                "negative_self_talk": [
                    "What would you say to a friend who talked about themselves the way you just did?",
                    "I hear you being really hard on yourself. What's one thing you've handled well recently?"
                ]
            },
            "behavioral_activation": {
                "avoidance": [
                    "What's the smallest step you could take toward this that would feel manageable?",
                    "Sometimes we avoid things because they feel overwhelming. What if we broke this into tiny pieces?"
                ],
                "procrastination": [
                    "What usually helps you get unstuck when you're in this headspace?",
                    "If you had to do just 2 minutes of this task, what would those 2 minutes look like?"
                ]
            },
            "motivational_interviewing": {
                "low_motivation": [
                    "What would need to change for this to feel more important to you?",
                    "On a scale of 1-10, how ready do you feel to work on this? What would move you up one point?"
                ],
                "ambivalence": [
                    "I hear part of you wants this and part of you has reservations. Tell me about both sides.",
                    "What would it mean for you if things stayed exactly as they are now?"
                ]
            },
            "strengths_based": {
                "building_confidence": [
                    "I'm hearing some real wisdom in how you handled that. What strengths did you use?",
                    "You've overcome challenges before. What inner resources helped you then?"
                ],
                "celebrating_progress": [
                    "That might seem small to you, but it represents real neural pathway changes in your brain.",
                    "These small consistent actions are literally rewiring your brain for success."
                ]
            }
        }
    
    def generate_enhanced_prompt(
        self, 
        user_message: str, 
        psychological_analysis: Dict[str, Any],
        response_strategy: Dict[str, Any],
        user_context: Dict[str, Any],
        conversation_history: List[Dict[str, Any]]
    ) -> str:
        """Generate streamlined, high-impact prompt"""
        
        # Extract key psychological data
        emotions = [state.value for state in psychological_analysis.get('emotional_state', [])]
        patterns = [pattern.value for pattern in psychological_analysis.get('cognitive_patterns', [])]
        
        # Build JSON psychological state
        psych_state = {
            "emotion": emotions[0] if emotions else "NEUTRAL",
            "pattern": patterns[0] if patterns else "NONE", 
            "motivation": psychological_analysis.get('motivation_level', 5),
            "technique": response_strategy.get('primary_technique', 'supportive')
        }
        
        # Extract top 3 memory snippets
        memory_snippets = self._get_top_memory_snippets(conversation_history)
        
        # Build the streamlined prompt
        prompt = f"""{self.base_personality}

CONTEXT BLOCKS  
<PSYCH_STATE>  
{psych_state}             # {{"emotion":"{emotions[0] if emotions else 'NEUTRAL'}","pattern":"{patterns[0] if patterns else 'NONE'}"}}  

<MEMORY>  
{memory_snippets}            # • "🔥 5-day streak" • "Win: client email Monday"  

<USER>  
{user_message}                # e.g. "I always mess everything up"

---  (everything above is hidden from the user)  ---

Now write your reply."""

        return prompt
    
    def _get_top_memory_snippets(self, conversation_history: List[Dict]) -> str:
        """Extract top 3 memory snippets with progress indicators"""
        if not conversation_history:
            return "• 🆕 New user - first conversation"
        
        # Get the most recent and relevant memories
        snippets = []
        for memory in conversation_history[-3:]:  # Last 3 memories
            if isinstance(memory, dict):
                memory_text = memory.get('memory', '')
                if memory_text and len(memory_text) > 10:  # Skip very short memories
                    # Add progress emojis based on content
                    emoji = self._get_memory_emoji(memory_text, memory.get('metadata', {}))
                    
                    # Truncate long memories
                    snippet = memory_text[:50] + "..." if len(memory_text) > 50 else memory_text
                    snippets.append(f"• {emoji} {snippet}")
        
        return '\n'.join(snippets) if snippets else "• 📝 Limited conversation history"
    
    def _get_memory_emoji(self, memory_text: str, metadata: Dict) -> str:
        """Get appropriate emoji for memory based on content and metadata"""
        memory_lower = memory_text.lower()
        
        # Success/positive indicators
        if any(word in memory_lower for word in ['completed', 'achieved', 'succeeded', 'won', 'did it']):
            return "🔥"
        elif any(word in memory_lower for word in ['streak', 'day', 'consistent']):
            return "⚡"
        elif any(word in memory_lower for word in ['breakthrough', 'insight', 'realized']):
            return "💡"
        elif any(word in memory_lower for word in ['better', 'improved', 'progress']):
            return "📈"
        elif any(word in memory_lower for word in ['struggling', 'difficult', 'hard']):
            return "💪"
        elif any(word in memory_lower for word in ['goal', 'plan', 'want to']):
            return "🎯"
        else:
            return "📝"
    
    def _extract_memory_insights(self, conversation_history: List[Dict]) -> str:
        """Extract key insights from conversation memory"""
        if not conversation_history:
            return "MEMORY CONTEXT: First interaction - focus on building rapport and understanding their goals."
        
        # Analyze conversation patterns
        themes = self._identify_conversation_themes(conversation_history)
        progress_markers = self._identify_progress_markers(conversation_history)
        
        return f"""MEMORY INSIGHTS:
- Key Themes: {', '.join(themes)}
- Progress Patterns: {progress_markers}
- Previous Breakthroughs: {self._identify_breakthroughs(conversation_history)}
- Recurring Challenges: {self._identify_patterns(conversation_history)}"""
    
    def _identify_conversation_themes(self, history: List[Dict]) -> List[str]:
        """Identify recurring themes in conversation"""
        themes = []
        
        # Look for common topics in memory data
        for memory in history:
            categories = memory.get('categories', [])
            themes.extend(categories)
        
        # Count frequency and return top themes
        theme_counts = {}
        for theme in themes:
            theme_counts[theme] = theme_counts.get(theme, 0) + 1
        
        return sorted(theme_counts.keys(), key=lambda x: theme_counts[x], reverse=True)[:3]
    
    def _identify_progress_markers(self, history: List[Dict]) -> str:
        """Identify progress patterns"""
        if len(history) < 2:
            return "Early stage - establishing baseline"
        
        # Simple progress analysis based on memory evolution
        recent_memories = history[-3:] if len(history) >= 3 else history
        progress_indicators = []
        
        for memory in recent_memories:
            memory_text = memory.get('memory', '')
            if any(word in memory_text.lower() for word in ['achieved', 'completed', 'succeeded', 'improved']):
                progress_indicators.append('positive_momentum')
            elif any(word in memory_text.lower() for word in ['struggling', 'stuck', 'difficult']):
                progress_indicators.append('facing_challenges')
        
        if 'positive_momentum' in progress_indicators:
            return "Building positive momentum"
        elif 'facing_challenges' in progress_indicators:
            return "Working through challenges"
        else:
            return "Steady progress"
    
    def _identify_breakthroughs(self, history: List[Dict]) -> str:
        """Identify breakthrough moments"""
        breakthroughs = []
        
        for memory in history:
            memory_text = memory.get('memory', '').lower()
            if any(word in memory_text for word in ['breakthrough', 'realized', 'insight', 'clarity']):
                breakthroughs.append(memory.get('memory', '')[:50] + "...")
        
        return '; '.join(breakthroughs[:2]) if breakthroughs else "Building toward breakthroughs"
    
    def _identify_patterns(self, history: List[Dict]) -> str:
        """Identify recurring challenge patterns"""
        patterns = []
        
        for memory in history:
            memory_text = memory.get('memory', '').lower()
            if any(word in memory_text for word in ['always', 'tends to', 'pattern of', 'usually']):
                patterns.append(memory.get('memory', '')[:40] + "...")
        
        return '; '.join(patterns[:2]) if patterns else "Still learning patterns"
    
    def _format_recent_conversation(self, history: List[Dict]) -> str:
        """Format recent conversation for context"""
        if not history:
            return "This is your first conversation with this user."
        
        recent_memories = history[-5:] if len(history) >= 5 else history
        formatted = []
        
        for memory in recent_memories:
            memory_text = memory.get('memory', '')
            timestamp = memory.get('created_at', '')
            formatted.append(f"- {memory_text} ({timestamp[:10]})")
        
        return "RECENT CONVERSATION HISTORY:\n" + "\n".join(formatted)
    
    def _select_therapeutic_approach(self, analysis: Dict, strategy: Dict) -> str:
        """Select specific therapeutic approach instructions"""
        
        primary_technique = strategy.get('primary_technique', 'supportive_coaching')
        
        approaches = {
            "cognitive_restructuring": """
COGNITIVE RESTRUCTURING APPROACH:
- Gently challenge the distorted thinking pattern you identified
- Use Socratic questioning: "What evidence supports/contradicts this thought?"
- Help them find a more balanced perspective
- Don't argue with their thoughts - guide them to examine the evidence themselves""",
            
            "behavioral_activation": """
BEHAVIORAL ACTIVATION APPROACH:
- Focus on small, specific actions they can take immediately
- Use the "2-minute rule" - suggest the smallest possible version
- Connect actions to their values and goals
- Build momentum through micro-wins""",
            
            "motivational_interviewing": """
MOTIVATIONAL INTERVIEWING APPROACH:
- Explore their ambivalence without pushing
- Ask open-ended questions about their motivations
- Reflect back their own arguments for change
- Strengthen their intrinsic motivation""",
            
            "stress_regulation": """
STRESS REGULATION APPROACH:
- Acknowledge their nervous system is activated
- Offer immediate grounding techniques (breathing, 5-4-3-2-1)
- Focus on what they can control right now
- Normalize their stress response""",
            
            "strengths_based_coaching": """
STRENGTHS-BASED APPROACH:
- Identify and reflect back their strengths and resources
- Connect current challenges to past successes
- Build self-efficacy by highlighting their capabilities
- Use appreciative inquiry methods"""
        }
        
        return approaches.get(primary_technique, approaches["strengths_based_coaching"])
    
    def create_crisis_intervention_prompt(self, user_message: str, user_context: Dict) -> str:
        """Create specialized prompt for crisis situations"""
        
        return f"""{self.base_personality}

CRISIS INTERVENTION MODE ACTIVATED

The user has indicated they may be in distress. Your response should:

1. IMMEDIATE SAFETY: Acknowledge their pain and validate their experience
2. PROFESSIONAL HELP: Gently suggest speaking with a mental health professional
3. CRISIS RESOURCES: Provide crisis hotline information if appropriate
4. STAY PRESENT: Offer immediate coping strategies
5. FOLLOW-UP: Encourage continued support

USER MESSAGE: "{user_message}"

RESPONSE APPROACH:
- Be warm, direct, and non-judgmental
- Validate their courage in reaching out
- Provide practical immediate support
- Emphasize that help is available
- Don't try to "fix" everything in one response

Remember: You're providing support, not therapy. Professional help may be needed."""
    
    def get_specialized_coach_prompt(self, coach_type: CoachType, user_context: Dict, conversation_history: List[Dict] = None) -> str:
        """
        Get specialized coach prompt based on the comprehensive system prompts document
        """
        # Extract user preferences and context from subscription data
        user_preferences = {
            'pronoun_style': user_context.get('communication_style', 'I'),
            'plan_type': user_context.get('plan_type', '3_month')
        }
        
        # Extract goals and challenges from subscription fields
        current_goals = []
        if user_context.get('personal_goals'):
            current_goals = [user_context.get('personal_goals')]
        
        recent_wins = []  # Will be populated from conversation history
        current_challenges = []
        if user_context.get('active_challenges'):
            current_challenges = [user_context.get('active_challenges')]
        
        # Extract wins, challenges, and affirmations from conversation history
        last_affirmations = []
        if conversation_history:
            for memory in conversation_history[-7:]:  # Last 7 interactions
                memory_text = memory.get('memory', '').lower()
                
                # Collect affirmations to avoid repeats
                if 'affirmation' in memory_text:
                    last_affirmations.append(memory.get('memory', ''))
                
                # Extract recent wins
                if any(word in memory_text for word in ['completed', 'achieved', 'succeeded', 'accomplished', 'won']):
                    recent_wins.append(memory.get('memory', '')[:50] + "...")
                
                # Extract current challenges from recent conversations
                if any(word in memory_text for word in ['struggling', 'difficult', 'challenge', 'hard', 'overwhelmed']):
                    current_challenges.append(memory.get('memory', '')[:50] + "...")
        
        # Create coaching context
        context = CoachingContext(
            user_id=user_context.get('id', ''),
            coach_type=coach_type,
            conversation_history=conversation_history or [],
            user_preferences=user_preferences,
            current_goals=current_goals,
            recent_wins=recent_wins,
            current_challenges=current_challenges,
            last_affirmations=last_affirmations
        )
        
        # Get specialized prompt
        return self.specialized_coaches.get_coach_prompt(context)
    
    def detect_coaching_scenario(self, user_message: str, conversation_history: List[Dict], current_hour: int) -> CoachType:
        """
        Enhanced coach detection with context awareness and confidence scoring
        """
        message_lower = user_message.lower()
        
        # Priority 1: Explicit coaching requests (highest confidence)
        explicit_patterns = {
            CoachType.WEEKLY_REFLECTION: [
                'weekly check', 'week review', 'how was my week', 'weekly reflection',
                'week summary', 'look back at week', 'weekly progress', 'this week'
            ],
            CoachType.DAY_PLANNING: [
                'plan my day', 'what should i do today', 'daily goals', 'today\'s plan',
                'organize my day', 'schedule today', 'daily priorities', 'plan today',
                'what\'s my plan', 'day structure', 'daily tasks'
            ],
            CoachType.ACCOUNTABILITY: [
                'how did i do', 'end of day', 'daily review', 'did i complete',
                'progress check', 'accomplished today', 'finished today',
                'goals update', 'check in', 'daily recap'
            ]
        }
        
        for coach_type, patterns in explicit_patterns.items():
            if any(phrase in message_lower for phrase in patterns):
                return coach_type
        
        # Priority 2: Context-based detection from conversation history
        recent_context = self._analyze_recent_context(conversation_history)
        
        # If user has been discussing goals/planning, lean toward planning coach
        if recent_context.get('planning_signals', 0) > 2:
            if any(word in message_lower for word in ['today', 'do', 'should', 'plan', 'want']):
                return CoachType.DAY_PLANNING
        
        # If user has been sharing progress, lean toward accountability
        if recent_context.get('progress_signals', 0) > 1:
            if any(word in message_lower for word in ['did', 'done', 'finished', 'completed']):
                return CoachType.ACCOUNTABILITY
        
        # Priority 3: Enhanced time-based detection with context
        coach_type = self._get_time_based_coach(current_hour, message_lower, recent_context)
        if coach_type != CoachType.ALWAYS_ON:
            return coach_type
        
        # Priority 4: Default to always-on companion for natural conversations
        return CoachType.ALWAYS_ON
    
    def _analyze_recent_context(self, conversation_history: List[Dict]) -> Dict[str, int]:
        """Analyze recent conversation for context signals"""
        context_signals = {
            'planning_signals': 0,
            'progress_signals': 0,
            'gratitude_signals': 0,
            'motivation_signals': 0,
            'reflection_signals': 0
        }
        
        # Look at last 5 interactions
        recent_memories = conversation_history[-5:] if len(conversation_history) >= 5 else conversation_history
        
        for memory in recent_memories:
            memory_text = memory.get('memory', '').lower()
            
            # Count planning signals
            if any(word in memory_text for word in ['goal', 'plan', 'want to', 'will do', 'schedule']):
                context_signals['planning_signals'] += 1
            
            # Count progress signals  
            if any(word in memory_text for word in ['completed', 'finished', 'done', 'achieved', 'accomplished']):
                context_signals['progress_signals'] += 1
                
            # Count gratitude signals
            if any(word in memory_text for word in ['grateful', 'thankful', 'appreciate', 'blessed']):
                context_signals['gratitude_signals'] += 1
                
            # Count motivation signals
            if any(word in memory_text for word in ['motivation', 'inspire', 'encourage', 'boost']):
                context_signals['motivation_signals'] += 1
                
            # Count reflection signals
            if any(word in memory_text for word in ['reflect', 'think about', 'looking back', 'learned']):
                context_signals['reflection_signals'] += 1
        
        return context_signals
    
    def _get_time_based_coach(self, current_hour: int, message_lower: str, context: Dict[str, int]) -> CoachType:
        """Enhanced time-based coach detection with context"""
        
        # Morning (6-10): Only affirmations if explicitly asked for
        if 6 <= current_hour <= 10:
            if any(word in message_lower for word in ['plan', 'schedule', 'organize', 'today']):
                return CoachType.DAY_PLANNING
            # Only return morning affirmation if they explicitly ask for motivation/affirmation
            if any(word in message_lower for word in ['affirmation', 'morning boost', 'daily motivation']):
                return CoachType.MORNING_AFFIRMATION
        
        # Late morning (10-12): Planning coach if they seem lost/unorganized
        elif 10 <= current_hour <= 12:
            if any(word in message_lower for word in ['lost', 'don\'t know', 'what should', 'confused']):
                return CoachType.DAY_PLANNING
        
        # Only trigger specialized coaches for very specific requests
        # Most conversations should go to always-on companion for natural flow
        
        return CoachType.ALWAYS_ON
    
    def _get_sentiment_based_coach(self, message_lower: str) -> CoachType:
        """Select coach based on message sentiment when no other signals are clear"""
        
        # If they're asking for motivation/boost
        if any(word in message_lower for word in ['motivation', 'inspire', 'boost', 'encourage', 'energy']):
            current_hour = datetime.now().hour
            if 6 <= current_hour <= 11:
                return CoachType.MORNING_AFFIRMATION
            elif 12 <= current_hour <= 17:
                return CoachType.MIDDAY_AFFIRMATION
            else:
                return CoachType.EVENING_AFFIRMATION
        
        # If they're sharing gratitude/appreciation
        if any(word in message_lower for word in ['grateful', 'thankful', 'appreciate', 'blessed', 'lucky']):
            return CoachType.GRATITUDE
        
        # If they're discussing goals/future
        if any(word in message_lower for word in ['goal', 'want to', 'planning', 'future', 'dream']):
            return CoachType.DAY_PLANNING
        
        # Default to always-on companion for general conversations
        return CoachType.ALWAYS_ON
