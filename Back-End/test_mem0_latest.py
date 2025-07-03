#!/usr/bin/env python3
"""
Test with latest mem0 API format (2024)
"""

import os
from dotenv import load_dotenv

load_dotenv()

def test_latest_format():
    """Test with the very latest mem0 API format"""
    
    print("🔍 Testing latest mem0 API format...")
    
    api_key = os.getenv("MEM0_API_KEY")
    
    # Try different import methods
    try:
        print("\n📦 Testing import method 1: from mem0 import MemoryClient")
        from mem0 import MemoryClient
        client = MemoryClient(api_key=api_key)
        print("✅ Import successful")
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False
    
    # Test 1: Minimal format
    try:
        print("\n📝 Test 1: Minimal message format...")
        messages = [
            {"role": "user", "content": "Hello world"}
        ]
        result = client.add(messages, user_id="test123")
        print(f"✅ Minimal format worked: {result}")
        return True
    except Exception as e:
        print(f"❌ Minimal format failed: {e}")
    
    # Test 2: Try without explicit user_id parameter name
    try:
        print("\n📝 Test 2: Positional user_id...")
        messages = [{"role": "user", "content": "Test message"}]
        result = client.add(messages, "test456")
        print(f"✅ Positional user_id worked: {result}")
        return True
    except Exception as e:
        print(f"❌ Positional user_id failed: {e}")
    
    # Test 3: Try with different message structure
    try:
        print("\n📝 Test 3: Different message structure...")
        result = client.add("Simple text message", user_id="test789")
        print(f"✅ Simple text worked: {result}")
        return True
    except Exception as e:
        print(f"❌ Simple text failed: {e}")
    
    # Test 4: Check account status with direct API call
    try:
        print("\n📝 Test 4: Direct API test...")
        import requests
        
        # Test direct API call
        response = requests.post(
            "https://api.mem0.ai/v1/memories",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "messages": [{"role": "user", "content": "API test"}],
                "user_id": "direct_test"
            }
        )
        
        print(f"📊 Status: {response.status_code}")
        print(f"📊 Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Direct API call worked!")
            return True
        elif response.status_code == 401:
            print("❌ Authentication failed")
        elif response.status_code == 402:
            print("❌ Payment required")
        elif response.status_code == 429:
            print("❌ Rate limit exceeded")
        else:
            print(f"❌ Unknown error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Direct API failed: {e}")
    
    return False

if __name__ == "__main__":
    success = test_latest_format()
    
    if success:
        print("\n🎉 Found working format!")
    else:
        print("\n❌ All formats failed")
        print("\n💡 This suggests:")
        print("1. 📧 Account needs email verification")
        print("2. 🔄 mem0 API changed recently")
        print("3. 🐛 Temporary service issue")
        print("4. 🔑 API key issue")
        print("\n🌐 Try logging into https://app.mem0.ai to verify account status")