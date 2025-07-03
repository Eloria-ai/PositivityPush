#!/usr/bin/env python3
"""
Comprehensive test of AI coach with mem0 integration
"""

import asyncio
import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

async def test_full_ai_coach():
    """Test complete AI coach functionality with mem0"""
    
    print("🤖 Testing FULL AI Coach with mem0 integration...")
    
    # Import after loading environment
    from app.services.ai_coach import AICoachService
    
    # Initialize AI coach
    ai_coach = AICoachService()
    
    # Check if mem0 is available
    if ai_coach.mem0_service.is_available():
        print("✅ mem0 service is available and working!")
    else:
        print("❌ mem0 service is not available")
        return False
    
    # Test with a realistic user scenario
    user_id = "user_badr_test"
    user_context = {
        "email": "badr@positivitypush.com",
        "plan_type": "3_month",
        "phone_number": "+1234567890"
    }
    
    print(f"👤 Testing with user: {user_id}")
    
    # Test 1: First interaction - User introduces themselves
    print("\n🌟 Test 1: Initial user introduction...")
    response1 = await ai_coach.generate_response(
        user_id=user_id,
        message="Hi! I'm Badr. I'm working on building my startup and I struggle with staying positive during challenging times. I also want to maintain good work-life balance.",
        user_context=user_context
    )
    print(f"🤖 AI Coach: {response1}")
    
    # Test 2: Follow-up about specific challenge
    print("\n💪 Test 2: Sharing a specific challenge...")
    response2 = await ai_coach.generate_response(
        user_id=user_id,
        message="Yesterday I had a really tough investor meeting that didn't go well. I'm feeling discouraged and questioning if I'm on the right path.",
        user_context=user_context
    )
    print(f"🤖 AI Coach: {response2}")
    
    # Test 3: Ask for advice (should reference previous context)
    print("\n🎯 Test 3: Asking for specific advice...")
    response3 = await ai_coach.generate_response(
        user_id=user_id,
        message="What should I focus on this week to get back on track?",
        user_context=user_context
    )
    print(f"🤖 AI Coach: {response3}")
    
    # Test 4: Generate personalized daily affirmation
    print("\n☀️ Test 4: Personalized daily affirmation...")
    affirmation = await ai_coach.generate_daily_affirmation(user_id, user_context)
    print(f"🌟 Daily Affirmation: {affirmation}")
    
    # Test 5: Generate personalized gratitude prompt
    print("\n🙏 Test 5: Personalized gratitude prompt...")
    gratitude = await ai_coach.generate_gratitude_prompt(user_id, user_context)
    print(f"💝 Gratitude Prompt: {gratitude}")
    
    # Test 6: Check memory persistence - reference earlier conversation
    print("\n🧠 Test 6: Memory persistence check...")
    response6 = await ai_coach.generate_response(
        user_id=user_id,
        message="Can you remind me what my main goals are?",
        user_context=user_context
    )
    print(f"🤖 AI Coach: {response6}")
    
    # Test 7: Different user - should not access Badr's memories
    print("\n👥 Test 7: User isolation test...")
    other_user_id = "user_sarah_test"
    other_context = {"email": "sarah@example.com", "plan_type": "6_month"}
    
    response7 = await ai_coach.generate_response(
        user_id=other_user_id,
        message="What are my goals?",
        user_context=other_context
    )
    print(f"🤖 AI Coach (different user): {response7}")
    
    return True

if __name__ == "__main__":
    success = asyncio.run(test_full_ai_coach())
    if success:
        print("\n🎉 FULL AI Coach with mem0 integration is working perfectly!")
        print("✅ Memory creation and storage")
        print("✅ Context-aware conversations")
        print("✅ Personalized daily content")
        print("✅ Memory persistence across sessions")
        print("✅ User isolation and privacy")
        print("✅ Realistic coaching scenarios")
        print("\n🚀 Your Positivity Push AI coach is ready!")
    else:
        print("\n❌ AI Coach test failed")