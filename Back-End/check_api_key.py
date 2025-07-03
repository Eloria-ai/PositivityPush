#!/usr/bin/env python3
"""
Check API key format and authentication
"""

import os
from dotenv import load_dotenv
import requests

load_dotenv()

def check_api_key():
    """Check API key format and authentication"""
    
    api_key = os.getenv("MEM0_API_KEY")
    print(f"🔑 API Key format: {api_key[:10]}...{api_key[-4:]}")
    print(f"📏 API Key length: {len(api_key)}")
    print(f"🔤 API Key prefix: {api_key[:5]}")
    
    # Expected format: m0-xxxxx (based on your key)
    if not api_key.startswith("m0-"):
        print("❌ API key doesn't start with 'm0-'")
        return False
    
    # Test different authentication methods
    print("\n🔍 Testing authentication methods...")
    
    # Method 1: Bearer token (standard)
    try:
        print("\n📝 Method 1: Bearer token...")
        response = requests.get(
            "https://api.mem0.ai/v1/memories",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            params={"user_id": "test"}
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:200]}")
        
        if response.status_code == 200:
            print("✅ Bearer token works!")
            return True
            
    except Exception as e:
        print(f"❌ Bearer token failed: {e}")
    
    # Method 2: API key in header
    try:
        print("\n📝 Method 2: API-Key header...")
        response = requests.get(
            "https://api.mem0.ai/v1/memories",
            headers={
                "API-Key": api_key,
                "Content-Type": "application/json"
            },
            params={"user_id": "test"}
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:200]}")
        
        if response.status_code == 200:
            print("✅ API-Key header works!")
            return True
            
    except Exception as e:
        print(f"❌ API-Key header failed: {e}")
    
    # Method 3: Check if we can use the SDK for reading but not writing
    try:
        print("\n📝 Method 3: SDK read test...")
        from mem0 import MemoryClient
        client = MemoryClient(api_key=api_key)
        
        # Try to get memories for alex (should work based on previous tests)
        memories = client.get_all(user_id="alex")
        print(f"✅ SDK can read: {len(memories)} memories found")
        
        # But SDK write fails
        try:
            result = client.add([{"role": "user", "content": "test"}], user_id="test")
            print(f"✅ SDK can write: {result}")
            return True
        except Exception as e:
            print(f"❌ SDK cannot write: {e}")
            print("🤔 This suggests read-only access or API version mismatch")
        
    except Exception as e:
        print(f"❌ SDK test failed: {e}")
    
    return False

if __name__ == "__main__":
    success = check_api_key()
    
    if not success:
        print("\n💡 Solutions:")
        print("1. 🔄 Regenerate API key in mem0 dashboard")
        print("2. 📧 Contact mem0 support about write permissions")
        print("3. 🔍 Check if account has write restrictions")
        print("4. ⏰ Wait and try again (temporary issue)")
        print("5. 🆙 Consider upgrading to paid plan")
        
        print("\n🔗 Try these:")
        print("• Visit https://app.mem0.ai/api-keys")
        print("• Delete and create new API key")
        print("• Check account status in dashboard")