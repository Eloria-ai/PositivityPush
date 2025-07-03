#!/usr/bin/env python3
"""
Quick mem0 test for terminal
"""

import os
from dotenv import load_dotenv
from mem0 import MemoryClient

# Load environment
load_dotenv()

def main():
    print("🧠 Testing mem0...")
    
    # Get API key
    api_key = os.getenv("MEM0_API_KEY")
    if not api_key:
        print("❌ MEM0_API_KEY not found in environment")
        return
    
    print(f"🔑 API Key: {api_key[:10]}...{api_key[-4:]}")
    
    # Initialize client
    client = MemoryClient(api_key=api_key)
    
    # Test conversation
    messages = [
        {"role": "user", "content": "Hi, I'm Badr. I'm building a startup and working on staying positive."},
        {"role": "assistant", "content": "Great to meet you Badr! Building a startup is exciting. I'm here to help you stay positive."}
    ]
    
    # Add memory
    print("\n📝 Adding memory...")
    result = client.add(messages, user_id="badr_test")
    print(f"✅ Added {len(result.get('results', []))} memories")
    
    # Search memory
    print("\n🔍 Searching memories...")
    search_result = client.search("startup positivity", user_id="badr_test")
    print(f"✅ Found {len(search_result)} memories")
    
    # Get all memories
    print("\n📋 All memories:")
    all_memories = client.get_all(user_id="badr_test")
    for i, memory in enumerate(all_memories, 1):
        print(f"  {i}. {memory.get('memory')}")
    
    print("\n🎉 mem0 is working!")

if __name__ == "__main__":
    main()