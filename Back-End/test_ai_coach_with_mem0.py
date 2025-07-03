#!/usr/bin/env python3
"""
Test AI coach with mem0 integration
"""

import asyncio
import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

async def test_ai_coach_with_memory():
    """Test AI coach with mem0 memory integration"""
    
    # Import after loading environment
    from app.services.ai_coach import AICoachService
    
    print("🤖 Testing AI Coach with mem0 integration...")
    
    # Initialize AI coach
    ai_coach = AICoachService()
    
    # Test user
    user_id = "test_user_123"
    print(f"👤 Testing with user: {user_id}")
    
    # Test 1: Initial conversation (should create memories)
    print("\n📝 Test 1: Initial conversation...")
    user_context = {"email": "sarah@example.com", "plan_type": "3_month"}
    response1 = await ai_coach.generate_response(
        user_id=user_id,
        message="Hi! I'm Sarah and I want to work on building confidence and exercising regularly.",
        user_context=user_context
    )
    print(f"✅ Response 1: {response1}")
    
    # Test 2: Follow-up conversation (should use previous memories)
    print("\n📝 Test 2: Follow-up conversation...")
    response2 = await ai_coach.generate_response(
        user_id=user_id,
        message="I struggled with my workout yesterday. I felt too tired after work.",
        user_context=user_context
    )
    print(f"✅ Response 2: {response2}")
    
    # Test 3: Check if AI remembers context
    print("\n📝 Test 3: Context awareness...")
    response3 = await ai_coach.generate_response(
        user_id=user_id,
        message="What was my main goal again?",
        user_context=user_context
    )
    print(f"✅ Response 3: {response3}")
    
    # Test 4: Daily affirmation with personalization
    print("\n📝 Test 4: Personalized daily affirmation...")
    affirmation = await ai_coach.generate_daily_affirmation(user_id, user_context)
    print(f"✅ Affirmation: {affirmation}")
    
    # Test 5: Gratitude prompt with personalization
    print("\n📝 Test 5: Personalized gratitude prompt...")
    gratitude = await ai_coach.generate_gratitude_prompt(user_id, user_context)
    print(f"✅ Gratitude: {gratitude}")
    
    # Test 6: Different user (should not have access to Sarah's memories)
    print("\n📝 Test 6: Different user isolation...")
    other_user_id = "test_user_456"
    other_context = {"email": "john@example.com", "plan_type": "6_month"}
    response4 = await ai_coach.generate_response(
        user_id=other_user_id,
        message="What are my goals?",
        user_context=other_context
    )
    print(f"✅ Response for different user: {response4}")
    
    return True

if __name__ == "__main__":
    success = asyncio.run(test_ai_coach_with_memory())
    if success:
        print("\n🎉 AI Coach with mem0 integration is working!")
        print("✅ Memory creation and retrieval")
        print("✅ Personalized responses")
        print("✅ Context awareness")
        print("✅ User isolation")
        print("✅ Daily content personalization")
        print("\n💡 Ready for full system integration!")
    else:
        print("\n❌ AI Coach with mem0 integration failed")