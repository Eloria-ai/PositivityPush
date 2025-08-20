"""
Post-Generation Message Validator
Enforces content quality rules, word limits, and vocabulary restrictions after AI generation.
"""

import re
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from app.logging_config import get_logger

logger = get_logger("app.services.message_validator")

@dataclass
class ValidationRule:
    """Single validation rule configuration"""
    max_words: int
    min_words: int = 0
    max_questions: int = 1
    banned_phrases: List[str] = None

@dataclass
class ValidationResult:
    """Result of message validation and correction"""
    is_valid: bool
    original_message: str
    corrected_message: str
    violations: List[str]
    changes_made: List[str]

class MessageValidator:
    """
    Post-generation message validator that enforces content quality rules.
    Designed for safe rollout with per-type feature flags.
    """
    
    def __init__(self, supabase_service):
        self.supabase = supabase_service
        
        # Feature flags for gradual rollout
        self.enabled_validations = {
            'word_count': True,      # Start with this - safest
            'question_count': True,  # Start with this - safest  
            'phrase_bans': False,    # Enable per type later
            'validation_logging': False  # Enable when ready for monitoring
        }
        
        # Per-message-type validation rules
        self.validation_rules = {
            'daily_affirmation': ValidationRule(
                max_words=22, min_words=15, max_questions=0,
                banned_phrases=['joy', 'victories'] if self.enabled_validations['phrase_bans'] else []
            ),
            'gratitude_prompt': ValidationRule(
                max_words=38, min_words=22, max_questions=1,
                banned_phrases=['joy', 'victories', 'blanket', 'embrace'] if self.enabled_validations['phrase_bans'] else []
            ),
            'day_planning': ValidationRule(
                max_words=30, min_words=20, max_questions=1,
                banned_phrases=['evening', 'reflect', 'rest'] if self.enabled_validations['phrase_bans'] else []
            ),
            'accountability_checkin': ValidationRule(
                max_words=40, min_words=20, max_questions=1,
                banned_phrases=['multiple', 'additionally'] if self.enabled_validations['phrase_bans'] else []
            ),
            'weekly_reflection': ValidationRule(
                max_words=120, min_words=80, max_questions=2,
                banned_phrases=[] if self.enabled_validations['phrase_bans'] else []
            ),
            'midday_affirmation': ValidationRule(
                max_words=25, min_words=15, max_questions=0,
                banned_phrases=['rest', 'evening'] if self.enabled_validations['phrase_bans'] else []
            ),
            'evening_affirmation': ValidationRule(
                max_words=25, min_words=15, max_questions=0,
                banned_phrases=['energy', 'momentum'] if self.enabled_validations['phrase_bans'] else []
            )
        }
        
        # Time-based vocabulary cooldown (60 minutes)
        self.cooldown_minutes = 60
        
    def validate_and_correct(self, message: str, message_type: str, user_id: str) -> ValidationResult:
        """
        Main validation method - checks and corrects message against enabled rules.
        Returns corrected message and violation details.
        """
        original_message = message
        violations = []
        changes_made = []
        
        # Get validation rules for this message type
        rules = self.validation_rules.get(message_type)
        if not rules:
            logger.debug(f"No validation rules for message type: {message_type}")
            return ValidationResult(True, original_message, message, [], [])
        
        # 1. Word count enforcement (enabled by default)
        if self.enabled_validations['word_count']:
            message, word_changes = self._enforce_word_count(message, rules.max_words, rules.min_words)
            if word_changes:
                changes_made.extend(word_changes)
        
        # 2. Question count enforcement (enabled by default)
        if self.enabled_validations['question_count']:
            message, question_changes = self._enforce_question_limit(message, rules.max_questions)
            if question_changes:
                violations.append(f"Exceeded {rules.max_questions} question limit")
                changes_made.extend(question_changes)
        
        # 3. Banned phrase detection (feature flagged)
        if self.enabled_validations['phrase_bans'] and rules.banned_phrases:
            message, phrase_changes = self._replace_banned_phrases(message, rules.banned_phrases, message_type, user_id)
            if phrase_changes:
                violations.append("Used banned vocabulary")
                changes_made.extend(phrase_changes)
        
        is_valid = len(violations) == 0
        
        if changes_made:
            logger.info(f"Message validation: {message_type} - Changes: {len(changes_made)}")
        
        return ValidationResult(
            is_valid=is_valid,
            original_message=original_message,
            corrected_message=message,
            violations=violations,
            changes_made=changes_made
        )
    
    def _enforce_word_count(self, message: str, max_words: int, min_words: int) -> Tuple[str, List[str]]:
        """Enforce word count limits with intelligent truncation"""
        words = message.strip().split()
        word_count = len(words)
        changes = []
        
        if word_count > max_words:
            # Intelligent truncation at sentence boundaries
            sentences = re.split(r'[.!?]+', message)
            truncated = ""
            current_words = 0
            
            for sentence in sentences:
                sentence_words = len(sentence.strip().split())
                if current_words + sentence_words <= max_words:
                    truncated += sentence + "."
                    current_words += sentence_words
                else:
                    break
            
            # If sentence truncation still too long, hard truncate
            truncated_words = truncated.split()
            if len(truncated_words) > max_words:
                truncated = " ".join(words[:max_words]) + "."
            
            message = truncated.strip()
            changes.append(f"Truncated from {word_count} to {len(message.split())} words")
            
        elif word_count < min_words:
            # Log minimum word count violation (don't auto-extend)
            changes.append(f"Below minimum: {word_count}/{min_words} words")
        
        return message, changes
    
    def _enforce_question_limit(self, message: str, max_questions: int) -> Tuple[str, List[str]]:
        """Enforce maximum question count - keep first question, remove others"""
        question_count = message.count('?')
        changes = []
        
        if question_count > max_questions:
            if max_questions == 0:
                # Remove all question marks for affirmations
                message = message.replace('?', '.')
                changes.append("Converted questions to statements")
            else:
                # Keep only the first N questions by truncating at first question end
                question_positions = [i for i, char in enumerate(message) if char == '?']
                if question_positions and len(question_positions) > max_questions:
                    cutoff_pos = question_positions[max_questions - 1] + 1
                    message = message[:cutoff_pos].strip()
                    if not message.endswith('.'):
                        message += '.'
                    changes.append(f"Reduced from {question_count} to {max_questions} questions")
        
        return message, changes
    
    def _replace_banned_phrases(self, message: str, banned_phrases: List[str], message_type: str, user_id: str) -> Tuple[str, List[str]]:
        """Replace banned phrases with alternatives based on message type"""
        changes = []
        message_lower = message.lower()
        
        # Check for recent usage across all message types (cooldown enforcement)
        recent_banned = self._get_recently_used_phrases(user_id, banned_phrases)
        all_banned = set(banned_phrases + recent_banned)
        
        # Simple replacement dictionary
        replacements = {
            'joy': 'peace', 'victories': 'progress', 'momentum': 'energy', 
            'blanket': 'comfort', 'embrace': 'welcome', 'evening': 'day',
            'reflect': 'focus', 'rest': 'work', 'multiple': 'next',
            'additionally': 'also'
        }
        
        for banned in all_banned:
            if banned.lower() in message_lower:
                replacement = replacements.get(banned.lower(), 'growth')
                # Case-preserving replacement (first occurrence only)
                pattern = re.compile(re.escape(banned), re.IGNORECASE)
                message = pattern.sub(replacement, message, count=1)
                changes.append(f"Replaced '{banned}' with '{replacement}'")
                break  # Only replace one per validation cycle
        
        return message, changes
    
    def _get_recently_used_phrases(self, user_id: str, phrases: List[str]) -> List[str]:
        """Get phrases recently used across all message types (cross-type cooldown)"""
        if not phrases:
            return []
            
        cutoff_time = (datetime.now() - timedelta(minutes=self.cooldown_minutes)).isoformat()
        recently_used = []
        
        try:
            # Query recent AI-generated messages for vocabulary usage
            result = self.supabase.client.table("conversations") \
                .select("content") \
                .eq("subscriber_id", user_id) \
                .eq("message_type", "assistant") \
                .gte("timestamp", cutoff_time) \
                .not_.ilike("content", "PATTERN_TRACK:%") \
                .limit(10) \
                .execute()
            
            for row in result.data:
                content_lower = row["content"].lower()
                for phrase in phrases:
                    if phrase.lower() in content_lower:
                        recently_used.append(phrase)
        
        except Exception as e:
            logger.warning(f"Failed to check recent phrase usage: {e}")
        
        return list(set(recently_used))
    
    async def log_validation_results(self, user_id: str, message_type: str, validation_result: ValidationResult):
        """Log validation results for monitoring (feature flagged)"""
        if not self.enabled_validations['validation_logging'] or not validation_result.changes_made:
            return
            
        try:
            validation_data = {
                "interaction_type": "message_validation",
                "message_type_validated": message_type,
                "validation_results": {
                    "original_length": len(validation_result.original_message.split()),
                    "final_length": len(validation_result.corrected_message.split()),
                    "violations": validation_result.violations,
                    "changes_made": validation_result.changes_made,
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            await self.supabase.log_conversation(
                subscriber_id=user_id,
                content=f"VALIDATION: {message_type}",
                message_type='assistant',
                context_used=validation_data
            )
            
        except Exception as e:
            logger.warning(f"Failed to log validation results: {e}")