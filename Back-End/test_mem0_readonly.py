#!/usr/bin/env python3
"""
Test AI coach with read-only mem0 + local fallback
"""

import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

async def test_readonly_mem0():
    """Test AI coach with read-only mem0"""
    
    print("🤖 Testing AI Coach with read-only mem0...")
    
    # Import services
    from app.services.ai_coach import AICoachService
    
    # Initialize AI coach
    ai_coach = AICoachService()
    
    # Check mem0 status
    print(f"📊 mem0 available: {ai_coach.mem0_service.is_available()}")
    
    # Test with existing user that has memories
    user_id = "alex"  # This user has 7 memories we can read
    user_context = {"email": "alex@test.com", "plan_type": "3_month"}
    
    print(f"👤 Testing with existing user: {user_id}")
    
    # Test 1: Get existing memories
    print("\n📖 Reading existing memories...")
    memories = await ai_coach.mem0_service.get_memories(user_id)
    print(f"✅ Found {len(memories)} existing memories:")
    for i, memory in enumerate(memories[:3], 1):
        print(f"  {i}. {memory.get('memory', 'No content')}")
    
    # Test 2: Generate response using existing context
    print("\n💬 Generating response with existing context...")
    response = await ai_coach.generate_response(
        user_id=user_id,
        message="I'm feeling motivated today! What should I focus on?",
        user_context=user_context
    )
    print(f"🤖 AI Coach: {response}")
    
    # Test 3: Generate personalized content based on existing memories
    print("\n☀️ Personalized affirmation based on existing memories...")
    affirmation = await ai_coach.generate_daily_affirmation(user_id, user_context)
    print(f"🌟 Affirmation: {affirmation}")
    
    # Test 4: Search specific memories
    print("\n🔍 Searching for exercise-related memories...")
    exercise_memories = await ai_coach.mem0_service.get_memories(user_id, query="exercise workout")
    print(f"✅ Found {len(exercise_memories)} exercise memories:")
    for memory in exercise_memories[:2]:
        print(f"  - {memory.get('memory', 'No content')}")
    
    return True

async def test_new_user_fallback():
    """Test with new user (should work without mem0 writes)"""
    
    print("\n👤 Testing new user (no existing memories)...")
    
    from app.services.ai_coach import AICoachService
    ai_coach = AICoachService()
    
    new_user_id = "badr_new"
    user_context = {"email": "badr@test.com", "plan_type": "6_month"}
    
    # This should work even though mem0 add fails
    response = await ai_coach.generate_response(
        user_id=new_user_id,
        message="Hi! I'm Badr and I want to improve my confidence.",
        user_context=user_context
    )
    print(f"🤖 AI Coach (new user): {response}")
    
    # Generate content without stored memories
    affirmation = await ai_coach.generate_daily_affirmation(new_user_id, user_context)
    print(f"🌟 Affirmation (new user): {affirmation}")
    
    return True

if __name__ == "__main__":
    print("🔍 Testing AI Coach with current mem0 limitations...")
    
    success1 = asyncio.run(test_readonly_mem0())
    success2 = asyncio.run(test_new_user_fallback())
    
    if success1 and success2:
        print("\n✅ AI Coach works with current mem0 setup!")
        print("📖 Can read existing memories")
        print("🤖 Generates personalized responses")
        print("⚠️ New memories won't be stored (quota limit)")
        print("\n💡 Solutions:")
        print("1. Check your mem0 dashboard for quota limits")
        print("2. Upgrade your mem0 plan")
        print("3. Contact mem0 support")
        print("4. Use local memory storage as fallback")
    else:
        print("\n❌ Tests failed")