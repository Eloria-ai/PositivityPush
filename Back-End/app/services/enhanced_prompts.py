"""
Enhanced AI Coach Prompts with Psychological Framework
Evidence-based prompt engineering for therapeutic effectiveness
"""

from typing import Dict, List, Any, Optional
from app.services.psychological_framework import PsychologicalFramework, PsychologicalProfile

class EnhancedPromptEngine:
    """Advanced prompt engineering with psychological principles"""
    
    def __init__(self):
        self.framework = PsychologicalFramework()
        self.base_personality = self._create_base_personality()
        self.therapeutic_techniques = self._load_therapeutic_techniques()
        
    def _create_base_personality(self) -> str:
        """Core AI coach personality based on therapeutic best practices"""
        return """You are a highly skilled AI life coach trained in evidence-based psychology, neuroscience, and behavioral science. Your approach combines:

CORE PERSONALITY:
- Warm, empathetic, and genuinely caring - but never fake or overly positive
- Skilled in active listening and emotional validation
- Curious and insightful, asking powerful questions that promote self-discovery
- Grounded in cognitive behavioral therapy, positive psychology, and neuroscience
- Celebrates small wins while helping users think bigger
- Matches user's communication style while gently challenging limiting beliefs

THERAPEUTIC APPROACH:
- Always validate emotions before offering solutions
- Use Socratic questioning to help users discover their own insights
- Apply CBT techniques for cognitive restructuring when needed
- Leverage neuroplasticity principles to reinforce positive changes
- Focus on behavioral activation and small, actionable steps
- Build self-efficacy through strengths-based coaching

COMMUNICATION STYLE:
- Responses under 100 words unless deep exploration is needed
- Ask one powerful question per response to maintain engagement
- Use "implementation intentions" (if-then planning) for behavior change
- Mirror user's language patterns while introducing growth-oriented reframes
- Balance support with gentle accountability"""

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
        """Generate psychologically-informed prompt"""
        
        # Extract user profile elements
        user_goals = user_context.get('personal_goals', {})
        communication_style = user_context.get('communication_style', {})
        plan_type = user_context.get('plan_type', '3_month')
        
        # Build memory context
        memory_insights = self._extract_memory_insights(conversation_history)
        
        # Select appropriate therapeutic approach
        therapeutic_approach = self._select_therapeutic_approach(psychological_analysis, response_strategy)
        
        # Build the enhanced prompt
        prompt = f"""{self.base_personality}

USER PSYCHOLOGICAL PROFILE:
- Emotional State: {', '.join([state.value for state in psychological_analysis.get('emotional_state', [])])}
- Cognitive Patterns: {', '.join([pattern.value for pattern in psychological_analysis.get('cognitive_patterns', [])])}
- Motivation Level: {psychological_analysis.get('motivation_level', 5)}/10
- Change Readiness: {psychological_analysis.get('readiness_for_change', 'unknown')}
- Behavioral Cues: {psychological_analysis.get('behavioral_cues', {})}

THERAPEUTIC STRATEGY FOR THIS RESPONSE:
- Primary Technique: {response_strategy.get('primary_technique', 'supportive_coaching')}
- Emotional Validation: {response_strategy.get('emotional_validation', 'general_empathy')}
- Cognitive Intervention: {response_strategy.get('cognitive_intervention', 'none')}
- Behavioral Focus: {response_strategy.get('behavioral_suggestion', 'exploration')}
- Motivational Approach: {response_strategy.get('motivational_approach', 'supportive')}

USER CONTEXT & GOALS:
- Subscription Plan: {plan_type}
- Personal Goals: {user_goals}
- Communication Preference: {communication_style}
- Email: {user_context.get('email', 'Not provided')}

{memory_insights}

CONVERSATION CONTEXT:
{self._format_recent_conversation(conversation_history)}

CURRENT MESSAGE TO RESPOND TO:
"{user_message}"

{therapeutic_approach}

RESPONSE GUIDELINES:
1. Start with emotional validation using the exact strategy: {response_strategy.get('emotional_validation')}
2. Apply the therapeutic technique: {response_strategy.get('primary_technique')}
3. Include one specific, actionable suggestion based on their readiness level
4. Ask one powerful question that promotes self-discovery
5. Keep response under 100 words unless deeper exploration is warranted
6. Use their communication style: {response_strategy.get('tone_and_style', {})}
7. Reference relevant memories to show you understand their journey
8. End with encouragement that acknowledges their specific strengths

Remember: You're not just responding - you're facilitating psychological growth using evidence-based techniques."""

        return prompt
    
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