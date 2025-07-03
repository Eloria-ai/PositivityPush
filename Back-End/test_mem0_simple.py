#!/usr/bin/env python3
"""
Simple mem0 test to verify the correct API format
"""

import os
import asyncio
from dotenv import load_dotenv
from mem0 import MemoryClient

# Load environment
load_dotenv()

async def test_simple_mem0():
    """Test mem0 with the exact format from their documentation"""
    
    # Initialize client
    client = MemoryClient(api_key=os.getenv("MEM0_API_KEY"))
    
    # Test the exact format they showed you
    messages = [
        {"role": "user", "content": "Hi, I'm Alex. I'm a vegetarian and I'm allergic to nuts."},
        {"role": "assistant", "content": "Hello Alex! I see that you're a vegetarian with a nut allergy."}
    ]
    
    try:
        print("🧠 Testing mem0 with exact documentation format...")
        
        # Try the format they showed you
        result = client.add(messages, user_id="alex")
        print(f"✅ Memory added successfully: {result}")
        
        # Try searching
        query = "What can I cook for dinner tonight?"
        search_result = client.search(query, user_id="alex")
        print(f"✅ Search result: {search_result}")
        
        return True
        
    except Exception as e:
        print(f"❌ mem0 test failed: {e}")
        
        # Try alternative format without user_id as keyword
        try:
            print("🔄 Trying alternative format...")
            result = client.add(messages, "alex")
            print(f"✅ Alternative format worked: {result}")
            return True
        except Exception as e2:
            print(f"❌ Alternative format also failed: {e2}")
            return False

if __name__ == "__main__":
    asyncio.run(test_simple_mem0())