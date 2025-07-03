#!/usr/bin/env python3
"""
Test mem0 with EXACT format from their instructions
"""

import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

def test_exact_format():
    """Test with the exact format from mem0 documentation"""
    
    # Use the EXACT format from their instructions
    from mem0 import MemoryClient

    client = MemoryClient(api_key="m0-G63SyERCPva150fpcKmBDp0k0yxUJ5EcfNlY6IGD")

    # EXACT format from their docs
    messages = [
        { "role": "user", "content": "Hi, I'm Alex. I'm a vegetarian and I'm allergic to nuts." },
        { "role": "assistant", "content": "Hello Alex! I see that you're a vegetarian with a nut allergy." }
    ]

    try:
        print("🧠 Testing EXACT format from mem0 docs...")
        
        # EXACT call from their docs
        result = client.add(messages, user_id="alex")
        print(f"✅ SUCCESS! Result: {result}")
        
        # Test search too
        query = "What can I cook for dinner tonight?"
        search_result = client.search(query, user_id="alex")
        print(f"✅ Search SUCCESS! Result: {search_result}")
        
        return True
        
    except Exception as e:
        print(f"❌ EXACT format also failed: {e}")
        
        # Let's check the raw response
        try:
            import requests
            print("\n🔍 Checking account status...")
            
            # Try a simple API test
            response = requests.get(
                "https://api.mem0.ai/v1/memories",
                headers={
                    "Authorization": f"Bearer m0-G63SyERCPva150fpcKmBDp0k0yxUJ5EcfNlY6IGD",
                    "Content-Type": "application/json"
                },
                params={"user_id": "test"}
            )
            print(f"📊 API Status: {response.status_code}")
            print(f"📊 Response: {response.text}")
            
        except Exception as api_e:
            print(f"❌ API test failed: {api_e}")
        
        return False

if __name__ == "__main__":
    success = test_exact_format()
    if not success:
        print("\n🤔 The exact format from mem0 docs failed too.")
        print("\n💡 This suggests:")
        print("1. 🔍 Account needs verification (check email)")
        print("2. 🔍 API key might be invalid or expired")
        print("3. 🔍 Account might have restrictions")
        print("4. 🔍 Service might be down")
        print("\n📧 Please check your email for verification")
        print("🌐 Try logging into https://app.mem0.ai")