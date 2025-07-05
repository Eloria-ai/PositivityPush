"""
Psychological Framework for Positivity Push AI Coach
Evidence-based psychology, neuroscience, and behavioral science integration
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import json

class CognitivePattern(Enum):
    """Common cognitive distortions from CBT"""
    ALL_OR_NOTHING = "all_or_nothing"
    CATASTROPHIZING = "catastrophizing"
    MENTAL_FILTER = "mental_filter"
    NEGATIVE_SELF_TALK = "negative_self_talk"
    SHOULD_STATEMENTS = "should_statements"
    LABELING = "labeling"
    FORTUNE_TELLING = "fortune_telling"
    MIND_READING = "mind_reading"

class EmotionalState(Enum):
    """Emotional states for tracking patterns"""
    OVERWHELMED = "overwhelmed"
    ANXIOUS = "anxious"
    FRUSTRATED = "frustrated"
    MOTIVATED = "motivated"
    CONFIDENT = "confident"
    PEACEFUL = "peaceful"
    EXCITED = "excited"
    DISCOURAGED = "discouraged"

class BehavioralTrigger(Enum):
    """Common behavioral triggers"""
    STRESS = "stress"
    DEADLINE_PRESSURE = "deadline_pressure"
    SOCIAL_SITUATIONS = "social_situations"
    MORNING_ROUTINE = "morning_routine"
    EVENING_WIND_DOWN = "evening_wind_down"
    SETBACKS = "setbacks"
    SUCCESS = "success"

@dataclass
class PsychologicalProfile:
    """User's psychological profile for personalization"""
    dominant_cognitive_patterns: List[CognitivePattern]
    emotional_patterns: Dict[str, List[EmotionalState]]
    behavioral_triggers: Dict[BehavioralTrigger, str]
    motivation_style: str  # "achievement", "affiliation", "autonomy"
    communication_preference: str  # "direct", "gentle", "analytical", "story-based"
    stress_response_type: str  # "fight", "flight", "freeze", "fawn"
    growth_mindset_level: int  # 1-10 scale
    self_efficacy_areas: Dict[str, int]  # Domain-specific confidence levels

class PsychologicalFramework:
    """Core psychological framework for AI coaching"""
    
    def __init__(self):
        self.cbt_techniques = self._load_cbt_techniques()
        self.positive_psychology_interventions = self._load_positive_psychology()
        self.neuroscience_principles = self._load_neuroscience_principles()
        self.behavioral_change_strategies = self._load_behavioral_strategies()
    
    def _load_cbt_techniques(self) -> Dict[str, Dict]:
        """CBT-based intervention techniques"""
        return {
            "cognitive_restructuring": {
                "trigger_phrases": ["I can't", "I'm terrible at", "I always", "I never"],
                "reframe_templates": [
                    "What evidence do I have for this thought?",
                    "What would I tell a friend in this situation?",
                    "What's a more balanced way to think about this?",
                    "How might this challenge help me grow?"
                ],
                "response_style": "curious_questioning"
            },
            "thought_stopping": {
                "trigger_phrases": ["spiraling", "can't stop thinking", "stuck in my head"],
                "techniques": [
                    "5-4-3-2-1 grounding exercise",
                    "Deep breathing with counting",
                    "Physical movement interrupt",
                    "Positive affirmation replacement"
                ]
            },
            "behavioral_activation": {
                "when_detecting": ["low_mood", "avoidance", "isolation"],
                "micro_actions": [
                    "Take 3 deep breaths",
                    "Step outside for 2 minutes",
                    "Text one person you care about",
                    "Do one small task you've been avoiding"
                ]
            }
        }
    
    def _load_positive_psychology(self) -> Dict[str, Any]:
        """Positive psychology interventions"""
        return {
            "strengths_spotting": {
                "character_strengths": [
                    "perseverance", "creativity", "kindness", "leadership",
                    "honesty", "bravery", "prudence", "gratitude", "hope"
                ],
                "spotting_phrases": ["I managed to", "I figured out", "I helped", "I created"]
            },
            "gratitude_interventions": {
                "three_good_things": "Name 3 good things that happened and why they were meaningful",
                "gratitude_letter": "Think of someone who helped you - how might you thank them?",
                "gratitude_visit": "Who could you appreciate more fully?"
            },
            "flow_cultivation": {
                "flow_indicators": ["lost track of time", "felt completely absorbed", "everything clicked"],
                "flow_enhancers": [
                    "Clear goals with immediate feedback",
                    "Balance challenge with skill level",
                    "Minimize distractions",
                    "Focus on process over outcome"
                ]
            }
        }
    
    def _load_neuroscience_principles(self) -> Dict[str, Any]:
        """Neuroscience-based coaching principles"""
        return {
            "neuroplasticity": {
                "repetition_emphasis": "Neural pathways strengthen with repetition",
                "small_changes": "Tiny consistent changes rewire the brain",
                "visualization": "Mental rehearsal creates real neural pathways"
            },
            "dopamine_optimization": {
                "micro_rewards": "Celebrate every small step forward",
                "progress_tracking": "Visual progress triggers dopamine release",
                "novelty": "New experiences stimulate brain growth"
            },
            "stress_regulation": {
                "breathing_techniques": [
                    "4-7-8 breathing for anxiety",
                    "Box breathing for focus",
                    "Coherent breathing for balance"
                ],
                "physical_techniques": [
                    "Progressive muscle relaxation",
                    "Cold water on wrists/face",
                    "Gentle neck/shoulder rolls"
                ]
            }
        }
    
    def _load_behavioral_strategies(self) -> Dict[str, Any]:
        """Behavioral change strategies"""
        return {
            "habit_formation": {
                "tiny_habits": "Start with 2-minute versions",
                "habit_stacking": "Attach new habit to existing routine",
                "environment_design": "Make good choices easier, bad choices harder"
            },
            "implementation_intentions": {
                "if_then_planning": "If X situation occurs, then I will do Y",
                "specificity": "Define exactly when, where, and how"
            },
            "social_support": {
                "accountability_partner": "Share goals with trusted person",
                "community": "Connect with others on similar journey",
                "modeling": "Learn from others who've succeeded"
            }
        }
    
    def analyze_message_psychology(self, message: str, user_history: List[Dict]) -> Dict[str, Any]:
        """Analyze psychological elements in user message"""
        analysis = {
            "emotional_state": self._detect_emotional_state(message),
            "cognitive_patterns": self._detect_cognitive_patterns(message),
            "behavioral_cues": self._detect_behavioral_cues(message),
            "motivation_level": self._assess_motivation_level(message),
            "readiness_for_change": self._assess_change_readiness(message, user_history)
        }
        return analysis
    
    def _detect_emotional_state(self, message: str) -> List[EmotionalState]:
        """Detect emotional states from message content"""
        message_lower = message.lower()
        detected_states = []
        
        emotion_keywords = {
            EmotionalState.OVERWHELMED: ["overwhelmed", "too much", "can't handle", "drowning"],
            EmotionalState.ANXIOUS: ["worried", "nervous", "anxious", "stressed", "scared"],
            EmotionalState.FRUSTRATED: ["frustrated", "annoyed", "stuck", "why can't I"],
            EmotionalState.MOTIVATED: ["excited", "ready", "motivated", "let's do this"],
            EmotionalState.CONFIDENT: ["confident", "I can", "I will", "ready to"],
            EmotionalState.DISCOURAGED: ["giving up", "pointless", "why bother", "defeated"]
        }
        
        for state, keywords in emotion_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                detected_states.append(state)
        
        return detected_states
    
    def _detect_cognitive_patterns(self, message: str) -> List[CognitivePattern]:
        """Detect cognitive distortions in message"""
        message_lower = message.lower()
        detected_patterns = []
        
        pattern_keywords = {
            CognitivePattern.ALL_OR_NOTHING: ["always", "never", "completely", "totally", "nothing"],
            CognitivePattern.CATASTROPHIZING: ["disaster", "terrible", "awful", "worst case"],
            CognitivePattern.NEGATIVE_SELF_TALK: ["I'm terrible", "I can't", "I'm not good"],
            CognitivePattern.SHOULD_STATEMENTS: ["should", "must", "have to", "supposed to"],
            CognitivePattern.FORTUNE_TELLING: ["will fail", "won't work", "going to be bad"]
        }
        
        for pattern, keywords in pattern_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                detected_patterns.append(pattern)
        
        return detected_patterns
    
    def _detect_behavioral_cues(self, message: str) -> Dict[str, Any]:
        """Detect behavioral patterns and triggers"""
        message_lower = message.lower()
        
        cues = {
            "avoidance": any(word in message_lower for word in ["avoiding", "putting off", "don't want to"]),
            "perfectionism": any(word in message_lower for word in ["perfect", "not good enough", "has to be right"]),
            "action_oriented": any(word in message_lower for word in ["going to", "will do", "plan to"]),
            "seeking_support": any(word in message_lower for word in ["help", "advice", "what should I"])
        }
        
        return cues
    
    def _assess_motivation_level(self, message: str) -> int:
        """Assess motivation level 1-10"""
        message_lower = message.lower()
        
        high_motivation_words = ["excited", "ready", "motivated", "can't wait", "let's go"]
        low_motivation_words = ["tired", "don't want", "giving up", "what's the point"]
        
        if any(word in message_lower for word in high_motivation_words):
            return 8
        elif any(word in message_lower for word in low_motivation_words):
            return 3
        else:
            return 5  # Neutral
    
    def _assess_change_readiness(self, message: str, user_history: List[Dict]) -> str:
        """Assess readiness for change (precontemplation, contemplation, preparation, action, maintenance)"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["already doing", "been working on", "maintaining"]):
            return "maintenance"
        elif any(word in message_lower for word in ["going to start", "plan to", "will begin"]):
            return "preparation"
        elif any(word in message_lower for word in ["thinking about", "considering", "maybe I should"]):
            return "contemplation"
        elif any(word in message_lower for word in ["don't see the point", "not ready", "maybe later"]):
            return "precontemplation"
        else:
            return "action"
    
    def generate_psychological_response_strategy(self, analysis: Dict[str, Any], user_profile: PsychologicalProfile) -> Dict[str, Any]:
        """Generate response strategy based on psychological analysis"""
        
        strategy = {
            "primary_technique": self._select_primary_technique(analysis, user_profile),
            "emotional_validation": self._craft_emotional_validation(analysis["emotional_state"]),
            "cognitive_intervention": self._select_cognitive_intervention(analysis["cognitive_patterns"]),
            "behavioral_suggestion": self._select_behavioral_intervention(analysis),
            "motivational_approach": self._select_motivational_approach(analysis["motivation_level"], user_profile),
            "tone_and_style": self._determine_response_style(user_profile)
        }
        
        return strategy
    
    def _select_primary_technique(self, analysis: Dict, profile: PsychologicalProfile) -> str:
        """Select primary therapeutic technique based on user state"""
        
        if analysis["motivation_level"] < 4:
            return "motivational_interviewing"
        elif analysis["cognitive_patterns"]:
            return "cognitive_restructuring"
        elif EmotionalState.OVERWHELMED in analysis["emotional_state"]:
            return "stress_regulation"
        elif analysis["behavioral_cues"]["avoidance"]:
            return "behavioral_activation"
        else:
            return "strengths_based_coaching"
    
    def _craft_emotional_validation(self, emotional_states: List[EmotionalState]) -> str:
        """Craft empathetic validation based on detected emotions"""
        
        if not emotional_states:
            return "I hear you"
        
        validation_templates = {
            EmotionalState.OVERWHELMED: "It sounds like you're dealing with a lot right now",
            EmotionalState.FRUSTRATED: "I can sense the frustration in your message",
            EmotionalState.ANXIOUS: "Those anxious feelings are completely understandable",
            EmotionalState.DISCOURAGED: "It's natural to feel discouraged when things feel hard"
        }
        
        primary_emotion = emotional_states[0]
        return validation_templates.get(primary_emotion, "I hear what you're going through")
    
    def _select_cognitive_intervention(self, patterns: List[CognitivePattern]) -> Optional[str]:
        """Select appropriate cognitive intervention"""
        
        if not patterns:
            return None
        
        interventions = {
            CognitivePattern.ALL_OR_NOTHING: "curious_questioning",
            CognitivePattern.CATASTROPHIZING: "probability_assessment",
            CognitivePattern.NEGATIVE_SELF_TALK: "self_compassion_reframe",
            CognitivePattern.SHOULD_STATEMENTS: "preference_vs_demand"
        }
        
        return interventions.get(patterns[0])
    
    def _select_behavioral_intervention(self, analysis: Dict) -> str:
        """Select behavioral intervention based on analysis"""
        
        if analysis["behavioral_cues"]["avoidance"]:
            return "micro_step_suggestion"
        elif analysis["readiness_for_change"] == "preparation":
            return "implementation_planning"
        elif analysis["motivation_level"] > 7:
            return "momentum_building"
        else:
            return "small_wins_focus"
    
    def _select_motivational_approach(self, motivation_level: int, profile: PsychologicalProfile) -> str:
        """Select motivational approach based on level and profile"""
        
        if motivation_level < 4:
            return "intrinsic_motivation_exploration"
        elif motivation_level > 7:
            return "goal_crystallization"
        else:
            return "confidence_building"
    
    def _determine_response_style(self, profile: PsychologicalProfile) -> Dict[str, str]:
        """Determine optimal response style for user"""
        
        return {
            "tone": profile.communication_preference,
            "length": "concise" if "direct" in profile.communication_preference else "detailed",
            "questioning_style": "socratic" if "analytical" in profile.communication_preference else "gentle_inquiry",
            "encouragement_level": "high" if profile.growth_mindset_level > 7 else "moderate"
        }