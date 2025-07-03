#!/usr/bin/env python3
"""
Debug mem0 API format issues
"""

import os
from dotenv import load_dotenv
from mem0 import MemoryClient

load_dotenv()

def test_different_formats():
    """Test different message formats to find what works"""
    
    api_key = os.getenv("MEM0_API_KEY")
    client = MemoryClient(api_key=api_key)
    
    print("🔍 Testing different mem0 message formats...")
    
    # Format 1: Simple user message only
    try:
        print("\n📝 Test 1: Single user message...")
        messages1 = [{"role": "user", "content": "Hello, I am testing mem0."}]
        result1 = client.add(messages1, user_id="test1")
        print(f"✅ Format 1 worked: {result1}")
        return True
    except Exception as e:
        print(f"❌ Format 1 failed: {e}")
    
    # Format 2: User + assistant pair (what we've been using)
    try:
        print("\n📝 Test 2: User + assistant pair...")
        messages2 = [
            {"role": "user", "content": "Hi, I'm testing."},
            {"role": "assistant", "content": "Hello! I'm here to help."}
        ]
        result2 = client.add(messages2, user_id="test2")
        print(f"✅ Format 2 worked: {result2}")
        return True
    except Exception as e:
        print(f"❌ Format 2 failed: {e}")
    
    # Format 3: Try with simpler user_id
    try:
        print("\n📝 Test 3: Simple user_id...")
        messages3 = [{"role": "user", "content": "Test message"}]
        result3 = client.add(messages3, user_id="user123")
        print(f"✅ Format 3 worked: {result3}")
        return True
    except Exception as e:
        print(f"❌ Format 3 failed: {e}")
    
    # Format 4: Try with metadata
    try:
        print("\n📝 Test 4: With metadata...")
        messages4 = [{"role": "user", "content": "Test with metadata"}]
        result4 = client.add(messages4, user_id="user123", metadata={"test": "true"})
        print(f"✅ Format 4 worked: {result4}")
        return True
    except Exception as e:
        print(f"❌ Format 4 failed: {e}")
    
    # Format 5: Check if we can at least search/get (to verify API works)
    try:
        print("\n📝 Test 5: Search existing memories...")
        search_result = client.search("test", user_id="alex")  # Use alex from earlier successful test
        print(f"✅ Search works: Found {len(search_result)} memories")
        
        all_memories = client.get_all(user_id="alex")
        print(f"✅ Get all works: Found {len(all_memories)} memories")
        
        if all_memories:
            print("📖 Existing memories:")
            for memory in all_memories[:3]:
                print(f"  - {memory.get('memory', 'No content')}")
        
        return "read_only"
    except Exception as e:
        print(f"❌ Even search failed: {e}")
    
    return False

if __name__ == "__main__":
    result = test_different_formats()
    
    if result == True:
        print("\n🎉 Found working format!")
    elif result == "read_only":
        print("\n⚠️ API works for reading but not writing")
        print("💡 This might be a quota limit, account restriction, or API change")
    else:
        print("\n❌ All formats failed")
        print("💡 Possible issues:")
        print("  - Account quota reached")
        print("  - API key permissions changed") 
        print("  - mem0 API format changed")
        print("  - Service temporarily down")