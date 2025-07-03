#!/usr/bin/env python3
"""
Test different mem0 approaches
"""

import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

def test_different_approaches():
    """Test different mem0 import approaches"""
    
    api_key = os.getenv("MEM0_API_KEY")
    print(f"🔑 Using API key: {api_key[:10]}...{api_key[-4:]}")
    
    # Approach 1: MemoryClient (what we've been using)
    try:
        print("\n📝 Testing MemoryClient...")
        from mem0 import MemoryClient
        client = MemoryClient(api_key=api_key)
        
        messages = [{"role": "user", "content": "Test message"}]
        result = client.add(messages, user_id="test_user")
        print(f"✅ MemoryClient worked: {result}")
        return "MemoryClient"
        
    except Exception as e:
        print(f"❌ MemoryClient failed: {e}")
    
    # Approach 2: Memory class 
    try:
        print("\n📝 Testing Memory class...")
        from mem0 import Memory
        memory = Memory(api_key=api_key)
        
        messages = [{"role": "user", "content": "Test message"}]
        result = memory.add(messages, user_id="test_user")
        print(f"✅ Memory class worked: {result}")
        return "Memory"
        
    except Exception as e:
        print(f"❌ Memory class failed: {e}")
    
    # Approach 3: Direct import
    try:
        print("\n📝 Testing direct import...")
        import mem0
        client = mem0.MemoryClient(api_key=api_key)
        
        messages = [{"role": "user", "content": "Test message"}]
        result = client.add(messages, user_id="test_user")
        print(f"✅ Direct import worked: {result}")
        return "Direct"
        
    except Exception as e:
        print(f"❌ Direct import failed: {e}")
    
    # Approach 4: Check available classes
    try:
        print("\n📝 Checking available classes...")
        import mem0
        print(f"Available attributes: {dir(mem0)}")
        
    except Exception as e:
        print(f"❌ Could not check attributes: {e}")
    
    return None

if __name__ == "__main__":
    working_approach = test_different_approaches()
    if working_approach:
        print(f"\n🎉 Working approach: {working_approach}")
    else:
        print("\n❌ No approach worked - likely an account/API key issue")
        print("\n💡 Next steps:")
        print("1. Check if your mem0 account is verified (check email)")
        print("2. Try creating a memory in the mem0 web dashboard first")
        print("3. Make sure you're using the correct API key")
        print("4. Contact mem0 support if the issue persists")