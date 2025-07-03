"""
Onboarding Prompts for Positivity Push
Guides new users through initial goal setting and personalization.
"""

WELCOME_MESSAGE_TEMPLATE = """
Generate a warm welcome message for a new Positivity Push user. Include:

STRUCTURE:
1. Enthusiastic welcome to Positivity Push
2. Brief explanation of what their AI coach does
3. Ask about their goals or what brought them here
4. Set positive, encouraging tone for the relationship

USER INFO:
- Plan: {plan_type}
- Email: {email}

STYLE:
- Warm and genuine excitement
- Personal but not overly familiar
- 60-80 words
- End with an engaging question about their goals
- Use one meaningful emoji

Create a welcome that makes them excited to start their coaching journey.
"""

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