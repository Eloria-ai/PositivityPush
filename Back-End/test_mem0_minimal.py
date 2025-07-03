#!/usr/bin/env python3
"""
Test mem0 with absolutely minimal approach
"""

from mem0 import MemoryClient

# Use your exact API key
client = MemoryClient(api_key="m0-G63SyERCPva150fpcKmBDp0k0yxUJ5EcfNlY6IGD")

# Exact format from docs
messages = [
    { "role": "user", "content": "Hi, I'm Alex. I'm a vegetarian and I'm allergic to nuts." },
    { "role": "assistant", "content": "Hello Alex! I see that you're a vegetarian with a nut allergy." }
]

print("🧠 Testing minimal mem0 add...")
try:
    # Try exactly as documented
    result = client.add(messages, user_id="alex")
    print(f"✅ SUCCESS: {result}")
    
    # Try search
    query = "What can I cook for dinner tonight?"
    search_result = client.search(query, user_id="alex")
    print(f"✅ Search worked: {search_result}")
    
except Exception as e:
    print(f"❌ Failed: {e}")
    print(f"Error type: {type(e)}")
    
    # Check if we can inspect the error more
    if hasattr(e, 'response'):
        print(f"Response details: {e.response}")
    if hasattr(e, 'args'):
        print(f"Error args: {e.args}")