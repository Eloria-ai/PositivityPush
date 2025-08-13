"""
Daily Content Prompts for Positivity Push
Templates for generating personalized affirmations, gratitude prompts, and check-ins.
"""

DAILY_AFFIRMATION_PROMPT = """
Create a personalized daily affirmation for this user. Make it:

REQUIREMENTS:
- Specific to their goals, challenges, or recent conversations (must reference at least one concrete detail)
- Empowering and actionable (not just "feel good" words)
- 15-22 words maximum (one idea only)
- Vary opening tokens from the last 7 days; do not start with the same 3 words as yesterday
- Start with "Today" or "This morning" or their name (but do not repeat the same opener more than twice a week)
- Include one concrete action or mindset they can practice

USER CONTEXT:
{user_context}

RECENT CONVERSATIONS:
{recent_memories}

AFFIRMATION STYLE:
- Personal and relevant to their situation
- Encouraging but realistic
- Focused on growth and action
- Uses their preferred communication style

Generate a single, concise morning affirmation that will genuinely inspire them today.
"""

GRATITUDE_PROMPT_TEMPLATE = """
Create an evening gratitude reflection prompt for this user. Make it:

REQUIREMENTS:
- Connected to their day, experiences, or current focus (must reference at least one concrete detail)
- 22-38 words maximum
- Encourages deeper reflection without requiring a typed reply
- Include one concrete noticing cue (sound, sensation, a person)
- No exclamation marks; one question max
- Vary opener from last 7 days

USER CONTEXT:
{user_context}

RECENT CONVERSATIONS:
{recent_memories}

PROMPT STYLE:
- Thoughtful and personal
- Helps them notice specific positive moments
- Connects to their values or goals
- Ends with a gentle question

Create a gratitude prompt that will help them end their day with appreciation and reflection.
"""

WEEKLY_REFLECTION_PROMPT = """
Create a personalized weekly reflection for this user. Include:

STRUCTURE (80–120 words total):
1. Acknowledge their week with one concrete callback (win, challenge, person, or event) from memory
2. Ask one meaningful question about their progress or experiences (one question max)
3. Offer one insight or encouragement based on their journey
4. Close with a forward-looking micro-step they can do in ≤2 minutes next week

USER CONTEXT:
{user_context}

WEEK'S CONVERSATIONS:
{weekly_memories}

REFLECTION STYLE:
- Warm and celebratory of progress made
- Honest about challenges without being negative
- Helps them see patterns and growth
- Natural, not scripted
- If insufficient week data, say: "Since we’re just getting started…" and shift to planning

Create a reflection that helps them appreciate their journey and feel motivated for what's next.
"""

CHECK_IN_PROMPTS = [
    "How has your energy been lately? What's been fueling you or draining you?",
    "What's one thing you've learned about yourself this week?",
    "How are you doing with [specific goal they mentioned]? Any wins to celebrate?",
    "What's been on your mind lately that you'd like to talk through?",
    "How has your mood been? Any patterns you've noticed?",
    "What's one thing you're looking forward to this week?",
    "How are you taking care of yourself these days?",
    "What would make this week feel successful for you?",
    "Is there anything you've been avoiding that we could tackle together?",
    "What's one small thing that's been bringing you joy lately?"
]

MOTIVATION_BOOSTERS = [
    "Remember why you started this journey - that motivation is still inside you",
    "Small steps count. Progress isn't always dramatic, but it's always valuable",
    "You've handled 100% of your difficult days so far. That's an amazing track record",
    "Growth happens in the spaces between comfort and overwhelm - you're in that sweet spot",
    "Your willingness to keep trying is a strength, not a given",
    "Every challenge you've faced has taught you something - you're wiser because of them",
    "You're exactly where you need to be, even if it doesn't feel like it right now",
    "The fact that you care this much shows how much heart you have",
    "You don't have to be perfect to make progress",
    "Your future self is grateful for the work you're doing today"
]

GOAL_SETTING_PROMPTS = [
    "What would feel like a meaningful win for you this week?",
    "If you could only focus on one thing this month, what would create the biggest positive impact?",
    "What's one habit that, if you developed it, would improve multiple areas of your life?",
    "What goal feels both exciting and achievable right now?",
    "If you were to make one small change that your future self would thank you for, what would it be?",
    "What's something you used to enjoy that you'd like to bring back into your life?",
    "What would help you feel more like yourself on a daily basis?",
    "What skill would you love to develop just for the joy of learning?",
    "What boundary would improve your wellbeing if you set it?",
    "What's one area where you'd like to be more consistent?"
]
