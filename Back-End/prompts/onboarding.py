"""
Onboarding Prompts for Positivity Push
Optimized prompts to reduce token costs while maintaining quality.
"""

# System prompts (sent once, not repeated)
SYSTEM_PROMPTS = {
    "time_extractor": """You are a time extraction assistant for Positivity Push AI coaching. 
Extract times from user messages and return JSON: {"time": "H:MM AM/PM", "confidence": "high/medium/low"} 
Use 12-hour AM/PM format. Handle casual expressions like "around 9", "maybe 7". 
If no clear time found, return {"time": null, "confidence": "low"}.""",
    
    "conversation_coach": """You are Maya, a warm AI life coach for Positivity Push. 
Be encouraging, personal but professional. Keep responses concise (40-60 words). 
Focus on helping users set up their personalized coaching schedule.
CRITICAL: Ask only ONE question per message. Do not re-ask the same question unless the prior value was not saved.""",
    
    "weekly_parser": """Extract day and time from user messages for weekly scheduling.
Return JSON: {"day": "monday/tuesday/etc", "time": "H:MM AM/PM"} or null values if unclear.
Use 12-hour AM/PM format only.
If AM/PM is already present in the user's message, DO NOT ask for clarification.
Normalize common typos (e.g., 'wednes'→'wednesday', 'thuesday'→'tuesday')."""
}

# Optimized welcome template (reduced from 630+ to ~200 tokens)
WELCOME_MESSAGE_TEMPLATE = """Welcome to Positivity Push! I'm your AI coach, ready to provide personalized daily support tailored to your goals and schedule.

Plan: {plan_type}
What brought you here today? What area of your life would you like to work on together?"""

GOAL_DISCOVERY_QUESTIONS = [
    "What made you decide to start this positivity journey? I'd love to understand what brought you here.",
    
    "What does your best day look like? Help me understand what we're working toward together.",
    
    "What's one area of your life where you'd love to feel more confident or positive?",
    
    "Are there any habits or mindsets you've been wanting to change but haven't found the right support for?",
    
    "What would make you feel proud of yourself at the end of each day?",
    
    "Tell me about a time when you felt really good about yourself. What was happening in your life then?",
    
    "What kind of support do you find most helpful when you're working toward something important?",
    
    "Is there a particular challenge or stress you're dealing with that you'd like to work through together?",
    
    "What does 'positivity' mean to you? Everyone has their own definition.",
    
    "If you could wave a magic wand and change one thing about how you feel on a daily basis, what would it be?"
]

COMMUNICATION_STYLE_QUESTIONS = [
    "Do you prefer gentle encouragement or more direct motivation? I want to support you in the way that works best.",
    
    "Are you more of a morning person or evening person? I'd love to time our check-ins well.",
    
    "When you're stressed, what usually helps you feel better - talking it through, getting practical advice, or just knowing someone cares?",
    
    "Do you like celebrating small wins or do you prefer to focus on the bigger picture?",
    
    "Are you working on anything specific right now, or are you more in an exploration phase?",
    
    "How do you usually handle setbacks? I want to know how to best support you when things get tough.",
    
    "What time of day do you usually feel most motivated or clear-headed?",
    
    "Do you prefer shorter daily check-ins or deeper weekly conversations, or a mix of both?"
]

ONBOARDING_FLOW_PROMPTS = {
    "initial_welcome": """
    🎉 Welcome to Positivity Push! I'm your personal AI coach, and I'm genuinely excited to be part of your journey toward greater positivity and wellbeing.
    
    I'm here to offer personalized encouragement, help you work through challenges, celebrate your wins, and provide daily support that's tailored specifically to you.
    
    To get started, I'd love to know: What made you decide to begin this positivity journey? What are you hoping we can work on together?
    """,
    
    "goal_setting": """
    That's wonderful insight. Understanding your 'why' helps me support you in the most meaningful way.
    
    Now I'm curious about your goals. They don't have to be huge or perfectly defined - even a general direction is perfect.
    
    What's one area of your life where you'd love to feel more positive, confident, or at peace?
    """,
    
    "communication_preferences": """
    I love that goal - it's something we can definitely work on together with the right approach and support.
    
    To make sure I'm the most helpful coach for you, can you tell me: When you're working toward something important, what kind of support helps you most? 
    
    For example, do you prefer gentle encouragement, practical strategies, accountability check-ins, or something else entirely?
    """,
    
    "schedule_preferences": """
    Perfect! That helps me understand how to best support your style.
    
    One last question to personalize your experience: Are you more of a morning person or evening person? 
    
    I'd love to send you daily affirmations and check-ins at times when they'll be most meaningful and helpful for you.
    """,
    
    "onboarding_complete": """
    Thank you for sharing all of that with me! I feel like I have a great foundation for supporting you on this journey.
    
    Here's what you can expect:
    • Daily personalized affirmations tailored to your goals
    • Evening gratitude prompts to help you reflect and appreciate progress
    • Weekly check-ins to celebrate wins and work through challenges
    • 24/7 support whenever you need encouragement or want to talk through something
    
    I'm here for you, and I'm already excited to see the positive changes you'll create. 
    
    Is there anything specific you'd like to work on this week to get started?
    """
}

PERSONALIZATION_FOLLOW_UPS = [
    "That's really helpful to know. How long have you been thinking about working on this?",
    
    "I can hear how important this is to you. What would it feel like if you made progress in this area?",
    
    "That makes perfect sense. What's worked for you before when you've tackled similar goals?",
    
    "I appreciate you being so open about this. What support would be most valuable as you work toward this?",
    
    "Thank you for sharing that. What would be a meaningful first step in this direction?",
    
    "That's a beautiful goal. How will you know when you're making progress toward it?",
    
    "I can see why that matters to you. What obstacles have you faced with this in the past?",
    
    "That sounds both meaningful and achievable. What's your biggest motivator for this change?",
    
    "I love how thoughtful you are about this. What would success look like for you?",
    
    "That resonates deeply. What would you tell a friend who had the same goal?"
]

# Optimized prompt builders (30-40% token reduction)
def build_time_extraction_prompt(message: str, context: str) -> list:
    """Build minimal prompt for time extraction"""
    return [
        {"role": "system", "content": SYSTEM_PROMPTS["time_extractor"]},
        {"role": "user", "content": f"Context: {context}\nUser: \"{message}\"\nExtract time (AM/PM format):"}
    ]

def build_conversation_prompt(message: str, step_context: str, user_name: str = "") -> list:
    """Build optimized conversational prompt"""
    user_prompt = f"Context: Collecting {step_context}\nUser said: \"{message}\"\nRespond warmly:"
    if user_name:
        user_prompt = f"{user_name}, " + user_prompt.lower()
    
    return [
        {"role": "system", "content": SYSTEM_PROMPTS["conversation_coach"]},
        {"role": "user", "content": user_prompt}
    ]

def build_weekly_parsing_prompt(message: str) -> list:
    """Build prompt for weekly reflection time parsing"""
    return [
        {"role": "system", "content": SYSTEM_PROMPTS["weekly_parser"]},
        {"role": "user", "content": f"User said: \"{message}\"\nParse day and time:"}
    ]

# Context mappings for dynamic prompts
STEP_CONTEXTS = {
    "day_planning": "morning planning time",
    "accountability_checkin": "evening check-in time", 
    "evening_gratitude": "bedtime gratitude time",
    "weekly_reflection": "weekly reflection schedule",
    "timezone_location": "timezone information"
}

# Quick response templates (no AI needed for simple confirmations)
QUICK_CONFIRMATIONS = {
    "time_saved": "Perfect! I've saved {time} for your {type}. ",
    "next_step": "Now, when would you like your {next_type}? ",
    "completion": "Great! Your personalized schedule is ready. I'll send you {message_types} at the times you chose. Ready to begin your positivity journey? 🌟"
}

# Time format examples for consistent AM/PM usage
TIME_FORMAT_EXAMPLES = {
    "morning": "9:00 AM",
    "afternoon": "3:00 PM", 
    "evening": "7:00 PM",
    "night": "9:00 PM"
}
