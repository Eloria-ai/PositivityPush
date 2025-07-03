#!/usr/bin/env python3
"""
Simple mem0 test with your .env.local configuration
"""

import os
from dotenv import load_dotenv
from mem0 import MemoryClient

# Load your .env.local file with absolute path
import pathlib
current_dir = pathlib.Path(__file__).parent
env_path = current_dir / '.env.local'
print(f"📁 Loading env from: {env_path}")
load_dotenv(env_path)

def test_mem0_simple():
    """Test mem0 with your configuration"""
    
    print("🔍 Testing mem0 with your .env.local configuration...")
    
    # Get API key from environment
    api_key = os.getenv("MEM0_API_KEY")
    print(f"📋 API Key: {api_key[:10] + '...' + api_key[-4:] if api_key else 'MISSING'}")
    
    # Debug: show all environment variables
    print(f"🔍 Debug - All env vars with MEM0:")
    for key, value in os.environ.items():
        if 'MEM0' in key:
            print(f"  {key} = {value[:10] + '...' + value[-4:] if value else 'EMPTY'}")
    
    if not api_key or api_key == "your-mem0-api-key":
        print("❌ mem0 API key not configured properly")
        return False
    
    try:
        # Initialize client
        print("🔌 Initializing MemoryClient...")
        client = MemoryClient(api_key=api_key)
        print("✅ Client initialized successfully")
        
        # Test adding a memory
        print("\n📝 Testing memory creation...")
        messages = [
            {"role": "user", "content": "Hello, I'm testing mem0 integration with my AI coach app."},
            {"role": "assistant", "content": "Great! I can help you test the memory functionality."}
        ]
        
        result = client.add(messages, user_id="test_user_badr")
        print(f"✅ Memory added successfully: {len(result.get('results', []))} memories created")
        
        # Test searching memories
        print("\n🔍 Testing memory search...")
        search_result = client.search("testing AI coach", user_id="test_user_badr")
        print(f"✅ Search successful: Found {len(search_result)} relevant memories")
        
        # Test getting all memories
        print("\n📋 Testing memory retrieval...")
        all_memories = client.get_all(user_id="test_user_badr")
        print(f"✅ Retrieved {len(all_memories)} total memories")
        
        # Show the memories
        print("\n📖 Your stored memories:")
        for i, memory in enumerate(all_memories[:3], 1):  # Show first 3
            print(f"  {i}. {memory.get('memory', 'No content')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_mem0_simple()
    if success:
        print("\n🎉 mem0 is working perfectly with your configuration!")
        print("✅ API key is valid")
        print("✅ Can create memories")
        print("✅ Can search memories")
        print("✅ Can retrieve memories")
        print("\n💡 Ready to integrate with your AI coach!")
    else:
        print("\n❌ mem0 test failed - check your configuration")