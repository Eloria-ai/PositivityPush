"""
Progress Tracking System for Positivity Push
Tracks user actions, streaks, and breakthrough moments like Wysa/Woebot
"""

import re
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

@dataclass
class ProgressMarker:
    """Individual progress event"""
    user_id: str
    action_type: str  # "completed_action", "check_in", "breakthrough", "streak"
    description: str
    timestamp: datetime
    emoji: str
    streak_count: Optional[int] = None

class ProgressTracker:
    """Tracks user progress and achievements like top mental health apps"""
    
    def __init__(self):
        self.completion_patterns = [
            r"✅", r"done", r"completed", r"finished", r"did it", 
            r"checked ✅", r"reply ✅", r"✅ done"
        ]
        
        self.streak_actions = [
            "morning_routine", "gratitude", "breathing", "exercise", 
            "journaling", "meditation", "affirmation"
        ]
    
    def detect_action_completion(self, message: str, user_memories: List[Dict]) -> Optional[ProgressMarker]:
        """Detect if user completed a suggested action"""
        message_lower = message.lower().strip()
        
        # Check for completion indicators
        if any(re.search(pattern, message_lower) for pattern in self.completion_patterns):
            return self._create_completion_marker(message, user_memories)
        
        # Check for specific action confirmations
        return self._detect_specific_actions(message_lower, user_memories)
    
    def _create_completion_marker(self, message: str, user_memories: List[Dict]) -> ProgressMarker:
        """Create progress marker for completed action"""
        
        # Try to identify what action was completed based on recent memories
        recent_action = self._get_recent_suggested_action(user_memories)
        
        return ProgressMarker(
            user_id="", # Will be set by caller
            action_type="completed_action",
            description=f"Completed: {recent_action or 'coaching action'}",
            timestamp=datetime.now(),
            emoji="🔥",
            streak_count=None
        )
    
    def _get_recent_suggested_action(self, user_memories: List[Dict]) -> Optional[str]:
        """Extract the most recent action that was suggested"""
        
        # Look through recent memories for action suggestions
        for memory in reversed(user_memories[-5:]):  # Last 5 memories
            memory_text = memory.get('memory', '').lower()
            
            # Common action patterns
            if 'write down' in memory_text:
                return "journaling exercise"
            elif 'breathe' in memory_text or 'breathing' in memory_text:
                return "breathing exercise"
            elif 'gratitude' in memory_text:
                return "gratitude practice"
            elif 'walk' in memory_text or 'step outside' in memory_text:
                return "movement break"
            elif 'affirmation' in memory_text:
                return "affirmation practice"
        
        return "mindfulness exercise"
    
    def _detect_specific_actions(self, message: str, user_memories: List[Dict]) -> Optional[ProgressMarker]:
        """Detect specific types of completed actions"""
        
        action_indicators = {
            "breathing": {"keywords": ["took deep breaths", "breathing exercise", "4-7-8"], "emoji": "🌬️"},
            "gratitude": {"keywords": ["grateful for", "thankful", "appreciate"], "emoji": "🙏"},
            "movement": {"keywords": ["went for walk", "exercised", "moved"], "emoji": "🚶"},
            "journaling": {"keywords": ["wrote down", "journaled", "wrote it"], "emoji": "📝"},
            "self_compassion": {"keywords": ["kind to myself", "self-compassion"], "emoji": "💝"}
        }
        
        for action_type, details in action_indicators.items():
            if any(keyword in message for keyword in details["keywords"]):
                return ProgressMarker(
                    user_id="",
                    action_type=action_type,
                    description=f"Practiced {action_type.replace('_', ' ')}",
                    timestamp=datetime.now(),
                    emoji=details["emoji"]
                )
        
        return None
    
    def calculate_streak(self, user_id: str, action_type: str, user_memories: List[Dict]) -> int:
        """Calculate streak for specific action type"""
        
        # Count consecutive days with this action type
        streak_count = 0
        current_date = datetime.now().date()
        
        # Look through memories for streak patterns
        for memory in reversed(user_memories):
            memory_metadata = memory.get('metadata', {})
            memory_date_str = memory_metadata.get('timestamp', memory_metadata.get('date', ''))
            
            if memory_date_str:
                try:
                    memory_date = datetime.fromisoformat(memory_date_str.replace('Z', '+00:00')).date()
                    
                    # Check if this memory represents the action type
                    if self._memory_contains_action(memory, action_type):
                        days_diff = (current_date - memory_date).days
                        
                        if days_diff == streak_count:
                            streak_count += 1
                        else:
                            break
                            
                except ValueError:
                    continue
        
        return streak_count
    
    def _memory_contains_action(self, memory: Dict, action_type: str) -> bool:
        """Check if memory contains evidence of specific action"""
        memory_text = memory.get('memory', '').lower()
        interaction_type = memory.get('metadata', {}).get('interaction_type', '')
        
        action_patterns = {
            "breathing": ["breathing", "breath", "4-7-8", "deep breath"],
            "gratitude": ["grateful", "gratitude", "thankful", "appreciate"],
            "movement": ["walk", "exercise", "movement", "step"],
            "journaling": ["wrote", "journal", "write down"],
            "completed_action": ["completed", "done", "finished", "✅"]
        }
        
        patterns = action_patterns.get(action_type, [])
        return any(pattern in memory_text for pattern in patterns) or interaction_type == action_type
    
    def generate_celebration_message(self, progress_marker: ProgressMarker) -> str:
        """Generate celebration message for completed actions"""
        
        celebrations = {
            "completed_action": [
                "🔥 Yes! You did it!",
                "⚡ Action completed!", 
                "💪 Way to follow through!",
                "🎉 Love seeing you take action!"
            ],
            "breathing": [
                "🌬️ Great job slowing down!",
                "🧘 Your nervous system thanks you!",
                "✨ Breath by breath, you're growing!"
            ],
            "gratitude": [
                "🙏 Gratitude shifts everything!",
                "💝 Your positive mindset is growing!",
                "✨ What we appreciate, appreciates!"
            ],
            "movement": [
                "🚶 Movement is medicine!",
                "💪 Your body and mind feel better!",
                "⚡ Energy boost activated!"
            ]
        }
        
        celebration_options = celebrations.get(
            progress_marker.action_type, 
            celebrations["completed_action"]
        )
        
        import random
        return random.choice(celebration_options)
    
    def should_suggest_streak_celebration(self, streak_count: int) -> bool:
        """Determine if streak milestone should be celebrated"""
        milestone_days = [3, 5, 7, 10, 14, 21, 30]
        return streak_count in milestone_days
    
    def generate_streak_message(self, action_type: str, streak_count: int) -> str:
        """Generate streak celebration message"""
        
        emojis = {
            3: "🔥", 5: "⚡", 7: "🌟", 10: "💎", 
            14: "🏆", 21: "👑", 30: "🎯"
        }
        
        emoji = emojis.get(streak_count, "🔥")
        
        return f"{emoji} {streak_count}-day {action_type.replace('_', ' ')} streak! You're building powerful habits!"
    
    def detect_breakthrough_moment(self, message: str, psychological_analysis: Dict) -> Optional[ProgressMarker]:
        """Detect breakthrough or insight moments"""
        
        breakthrough_indicators = [
            "i realized", "breakthrough", "aha moment", "it clicked", 
            "i understand now", "makes sense", "i see it", "clarity"
        ]
        
        message_lower = message.lower()
        
        if any(indicator in message_lower for indicator in breakthrough_indicators):
            return ProgressMarker(
                user_id="",
                action_type="breakthrough",
                description="Had an important insight",
                timestamp=datetime.now(),
                emoji="💡"
            )
        
        # Detect emotional state improvements
        emotions = psychological_analysis.get('emotional_state', [])
        motivation = psychological_analysis.get('motivation_level', 5)
        
        if motivation > 7 and any(emotion.value in ['MOTIVATED', 'CONFIDENT'] for emotion in emotions):
            return ProgressMarker(
                user_id="",
                action_type="mood_boost",
                description="Feeling motivated and confident",
                timestamp=datetime.now(),
                emoji="🚀"
            )
        
        return None