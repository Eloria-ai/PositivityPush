#!/usr/bin/env python3
"""
Test new mem0 API key
"""

import os
from dotenv import load_dotenv
from mem0 import MemoryClient

load_dotenv()

def test_new_key():
    """Test new API key functionality"""
    
    api_key = os.getenv("MEM0_API_KEY")
    print(f"🔑 Testing new API key: {api_key[:10]}...{api_key[-4:]}")
    
    try:
        # Initialize client
        client = MemoryClient(api_key=api_key)
        
        # Test write (should work now)
        print("\n📝 Testing memory creation...")
        messages = [
            {"role": "user", "content": "Testing new API key - this should work now!"},
            {"role": "assistant", "content": "Great! The new API key is working perfectly."}
        ]
        
        result = client.add(messages, user_id="new_key_test")
        print(f"✅ SUCCESS! Memory created: {result}")
        
        # Test read
        print("\n📖 Testing memory retrieval...")
        memories = client.get_all(user_id="new_key_test")
        print(f"✅ Retrieved {len(memories)} memories")
        
        # Test search
        print("\n🔍 Testing memory search...")
        search_result = client.search("API key", user_id="new_key_test")
        print(f"✅ Search found {len(search_result)} memories")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_new_key()
    
    if success:
        print("\n🎉 NEW API KEY WORKS PERFECTLY!")
        print("✅ Can create memories")
        print("✅ Can read memories") 
        print("✅ Can search memories")
        print("\n🚀 Your mem0 integration is now fully functional!")
    else:
        print("\n❌ New API key still has issues")
        print("📧 Contact mem0 support if problems persist")