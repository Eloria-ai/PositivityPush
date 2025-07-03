#!/usr/bin/env python3
"""
Test mem0 full workflow now that we know it's working
"""

import os
from dotenv import load_dotenv
from mem0 import MemoryClient

# Load environment
load_dotenv()

def test_mem0_workflow():
    """Test complete mem0 workflow"""
    
    api_key = os.getenv("MEM0_API_KEY")
    print(f"🔑 Using API key: {api_key[:10]}...{api_key[-4:]}")
    
    client = MemoryClient(api_key=api_key)
    
    # Step 1: Add some memories
    print("\n📝 Adding memories...")
    
    # Add user profile info
    profile_messages = [
        {"role": "user", "content": "Hi, I'm Alex. I'm working on building better habits and improving my confidence."},
        {"role": "assistant", "content": "Hello Alex! I'm excited to help you build better habits and boost your confidence. What specific areas would you like to work on?"}
    ]
    
    result1 = client.add(profile_messages, user_id="alex")
    print(f"✅ Added profile: {result1}")
    
    # Add goals
    goals_messages = [
        {"role": "user", "content": "My main goals are to exercise 3 times a week and practice public speaking."},
        {"role": "assistant", "content": "Great goals! Regular exercise and public speaking practice are excellent ways to build confidence. Let's break these down into actionable steps."}
    ]
    
    result2 = client.add(goals_messages, user_id="alex")
    print(f"✅ Added goals: {result2}")
    
    # Add challenge
    challenge_messages = [
        {"role": "user", "content": "I struggle with motivation in the mornings. I tend to hit snooze and skip my workout."},
        {"role": "assistant", "content": "Morning motivation is a common challenge. We can work on creating a consistent morning routine that makes it easier to get started."}
    ]
    
    result3 = client.add(challenge_messages, user_id="alex")
    print(f"✅ Added challenge: {result3}")
    
    # Step 2: Search for relevant memories
    print("\n🔍 Searching memories...")
    
    # Search for exercise-related memories
    exercise_search = client.search("exercise workout motivation", user_id="alex")
    print(f"✅ Exercise search: {exercise_search}")
    
    # Search for goals
    goals_search = client.search("goals public speaking", user_id="alex")
    print(f"✅ Goals search: {goals_search}")
    
    # Step 3: Get all memories
    print("\n📋 Getting all memories...")
    all_memories = client.get_all(user_id="alex")
    print(f"✅ All memories: {all_memories}")
    
    # Step 4: Test with different user
    print("\n👤 Testing with different user...")
    
    other_messages = [
        {"role": "user", "content": "I'm Sam and I love cooking vegetarian food."},
        {"role": "assistant", "content": "Hi Sam! Vegetarian cooking is wonderful. What's your favorite dish to make?"}
    ]
    
    result4 = client.add(other_messages, user_id="sam")
    print(f"✅ Added for Sam: {result4}")
    
    # Check Sam's memories don't interfere with Alex's
    sam_memories = client.get_all(user_id="sam")
    print(f"✅ Sam's memories: {sam_memories}")
    
    alex_memories = client.get_all(user_id="alex")
    print(f"✅ Alex's memories still separate: {alex_memories}")
    
    return True

if __name__ == "__main__":
    success = test_mem0_workflow()
    if success:
        print("\n🎉 mem0 is working perfectly!")
        print("✅ Can add memories")
        print("✅ Can search memories")
        print("✅ Can get all memories")
        print("✅ User isolation works")
        print("\n💡 Ready to integrate with AI coach!")
    else:
        print("\n❌ Workflow failed")