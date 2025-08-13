"""
Lightweight Pattern Tracker for Anti-Repetition
Tracks message patterns to prevent repetitive content in AI-generated messages.
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
from app.logging_config import get_logger

logger = get_logger("app.services.pattern_tracker")

@dataclass
class MessagePattern:
    """Lightweight pattern data for anti-repetition"""
    opener: str  # First 3 words
    full_opener: str  # First 6 words
    theme: str  # Main theme/topic
    structure: str  # 'question', 'statement', 'command'
    timestamp: str  # ISO format
    
class PatternTracker:
    """
    Lightweight anti-repetition tracker that integrates cleanly with existing infrastructure.
    Fixes integration gaps identified in the review.
    """
    
    def __init__(self, supabase_service):
        self.supabase = supabase_service
        # Feature flags for easy rollback per message type
        self.enabled_types = {
            'daily_affirmation': True,
            'gratitude_prompt': True, 
            'weekly_reflection': True,
            'midday_affirmation': True,
            'evening_affirmation': True,
            'accountability_checkin': False,  # Start with core types only
            'day_planning': False
        }
    
    def extract_pattern(self, message: str) -> MessagePattern:
        """Extract pattern components from generated message"""
        words = message.strip().split()
        
        return MessagePattern(
            opener=" ".join(words[:3]).lower() if len(words) >= 3 else " ".join(words).lower(),
            full_opener=" ".join(words[:6]).lower() if len(words) >= 6 else " ".join(words).lower(),
            theme=self._extract_theme(message),
            structure=self._classify_structure(message),
            timestamp=datetime.now().isoformat()
        )
    
    def _classify_structure(self, message: str) -> str:
        """Classify rhetorical structure"""
        msg = message.strip().lower()
        if msg.endswith('?'):
            return 'question'
        elif any(msg.startswith(cmd) for cmd in ['take', 'remember', 'notice', 'let', 'breathe']):
            return 'command'
        return 'statement'
    
    def _extract_theme(self, message: str) -> str:
        """Extract main theme using keyword matching"""
        msg_lower = message.lower()
        
        themes = {
            'confidence': ['confident', 'capable', 'strong', 'powerful', 'courage'],
            'gratitude': ['grateful', 'thankful', 'appreciate', 'blessed'],
            'growth': ['grow', 'learn', 'progress', 'develop', 'improve'],
            'resilience': ['overcome', 'bounce back', 'endure', 'resilient'],
            'focus': ['focus', 'clarity', 'concentrate', 'attention'],
            'people': ['friend', 'family', 'person', 'someone', 'connect'],
            'peace': ['calm', 'peaceful', 'quiet', 'rest', 'breathe'],
            'action': ['step', 'move', 'do', 'achieve', 'accomplish']
        }
        
        for theme, keywords in themes.items():
            if any(keyword in msg_lower for keyword in keywords):
                return theme
        return 'general'
    
    async def store_pattern(self, user_id: str, message_type: str, message: str) -> bool:
        """Store pattern using updated log_conversation with context_used"""
        # Feature flag guard
        if not self.enabled_types.get(message_type, False):
            return True
            
        try:
            pattern = self.extract_pattern(message)
            
            # Use assistant type with PATTERN_TRACK prefix (schema only allows user/assistant)
            # Store minimal data in context_used for efficient querying
            context_data = {
                "interaction_type": "pattern_tracking",
                "message_type_tracked": message_type,
                "pattern": {
                    "opener": pattern.opener,
                    "full_opener": pattern.full_opener,
                    "theme": pattern.theme,
                    "structure": pattern.structure,
                    "timestamp": pattern.timestamp
                }
            }
            
            await self.supabase.log_conversation(
                subscriber_id=user_id,
                content=f"PATTERN_TRACK: {message_type}",  # Stable discriminator
                message_type='assistant',  # Schema compliance
                context_used=context_data
            )
            
            logger.debug(f"Pattern stored: {user_id}/{message_type} - {pattern.opener}")
            return True
            
        except Exception as e:
            logger.error(f"Pattern storage failed for {user_id}: {e}")
            return False
    
    async def get_recent_patterns(self, user_id: str, message_type: str, days: int = 7) -> List[MessagePattern]:
        """Get recent patterns with stable filtering (no LIKE queries)"""
        try:
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            # Use PATTERN_TRACK content prefix for stable filtering
            result = self.supabase.client.table("conversations") \
                .select("context_used, timestamp") \
                .eq("subscriber_id", user_id) \
                .eq("message_type", "assistant") \
                .like("content", "PATTERN_TRACK%") \
                .gte("timestamp", cutoff_date) \
                .order("timestamp", desc=True) \
                .execute()
            
            patterns = []
            for row in result.data:
                try:
                    context_data = json.loads(row["context_used"]) if row["context_used"] else {}
                    
                    # Filter by tracked message type
                    if context_data.get("message_type_tracked") == message_type:
                        pattern_data = context_data.get("pattern", {})
                        if pattern_data:
                            patterns.append(MessagePattern(
                                opener=pattern_data["opener"],
                                full_opener=pattern_data["full_opener"],
                                theme=pattern_data["theme"],
                                structure=pattern_data["structure"],
                                timestamp=pattern_data["timestamp"]
                            ))
                except (json.JSONDecodeError, KeyError):
                    continue
            
            logger.debug(f"Retrieved {len(patterns)} patterns for {user_id}/{message_type}")
            return patterns
            
        except Exception as e:
            logger.error(f"Pattern retrieval failed for {user_id}: {e}")
            return []
    
    async def generate_anti_repetition_addon(self, user_id: str, message_type: str) -> str:
        """Generate anti-repetition instructions for prompt enhancement"""
        # Feature flag guard
        if not self.enabled_types.get(message_type, False):
            return ""
            
        patterns = await self.get_recent_patterns(user_id, message_type)
        
        if not patterns:
            return "\nVARIETY: Fresh content - no recent patterns to avoid."
        
        # Build avoidance instructions
        openers = [p.opener for p in patterns[-5:]]  # Last 5 openers
        themes = [p.theme for p in patterns[-3:]]    # Last 3 themes
        
        instructions = ["\nANTI-REPETITION RULES:"]
        
        if openers:
            instructions.append(f"• AVOID recent openers: {', '.join(set(openers))}")
        
        theme_counts = {}
        for theme in themes:
            theme_counts[theme] = theme_counts.get(theme, 0) + 1
        overused = [t for t, c in theme_counts.items() if c >= 2]
        if overused:
            instructions.append(f"• AVOID overused themes: {', '.join(overused)}")
        
        # Add variation guidance by message type
        if message_type == 'daily_affirmation':
            instructions.append("• ROTATE themes: confidence → growth → resilience → focus → gratitude")
        elif message_type == 'gratitude_prompt':
            instructions.append("• ROTATE focus: people → experiences → simple joys → growth → peace")
        elif message_type == 'weekly_reflection':
            instructions.append("• ROTATE structure: celebration → insight → pattern recognition → forward focus")
        elif message_type == 'midday_affirmation':
            instructions.append("• ROTATE themes: energy → focus → motivation → strength → balance")
        elif message_type == 'evening_affirmation':
            instructions.append("• ROTATE themes: self-forgiveness → gratitude → peace → progress → hope")
        
        return "\n".join(instructions)
    
    async def cleanup_old_patterns(self, days: int = 14) -> int:
        """Clean up old pattern entries"""
        try:
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            result = self.supabase.client.table("conversations") \
                .delete() \
                .eq("message_type", "assistant") \
                .like("content", "PATTERN_TRACK%") \
                .lt("timestamp", cutoff_date) \
                .execute()
            
            count = len(result.data) if result.data else 0
            logger.info(f"Cleaned {count} old pattern entries")
            return count
            
        except Exception as e:
            logger.error(f"Pattern cleanup failed: {e}")
            return 0