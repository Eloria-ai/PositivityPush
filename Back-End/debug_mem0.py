#!/usr/bin/env python3
"""
Debug mem0 API issues
"""

import os
from dotenv import load_dotenv
from mem0 import MemoryClient

# Load environment
load_dotenv()

def debug_mem0():
    """Debug mem0 step by step"""
    
    print("🔍 Debugging mem0 API...")
    
    # Check API key
    api_key = os.getenv("MEM0_API_KEY")
    print(f"📋 API Key: {api_key[:10]}...{api_key[-4:] if api_key and len(api_key) > 14 else 'INVALID'}")
    
    if not api_key or api_key == "your-mem0-api-key":
        print("❌ Invalid API key")
        return False
    
    try:
        # Initialize client
        print("🔌 Initializing MemoryClient...")
        client = MemoryClient(api_key=api_key)
        print("✅ Client initialized")
        
        # Try the simplest possible request
        print("📝 Testing simplest memory creation...")
        simple_messages = [
            {"role": "user", "content": "Hello, this is a test message"}
        ]
        
        # Try with required user_id parameter
        result = client.add(simple_messages, user_id="test_user")
        print(f"✅ Simple add worked: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        
        # Check if it's an authentication error
        if "authentication" in str(e).lower() or "unauthorized" in str(e).lower():
            print("🔑 This looks like an authentication issue")
            print("💡 Please verify your API key is correct and has permissions")
        
        elif "bad request" in str(e).lower():
            print("📋 This is a request format issue")
            print("💡 Let's check if we need additional parameters")
            
            # Try with explicit user_id
            try:
                print("🔄 Trying with explicit user_id...")
                result = client.add(simple_messages, user_id="debug_user")
                print(f"✅ With user_id worked: {result}")
                return True
            except Exception as e2:
                print(f"❌ Still failed: {e2}")
                
                # Try with different message format
                try:
                    print("🔄 Trying different message format...")
                    alt_messages = [
                        {"role": "user", "content": "Test"},
                        {"role": "assistant", "content": "Response"}
                    ]
                    result = client.add(alt_messages, user_id="debug_user")
                    print(f"✅ Alternative format worked: {result}")
                    return True
                except Exception as e3:
                    print(f"❌ All formats failed: {e3}")
        
        return False

if __name__ == "__main__":
    success = debug_mem0()
    if not success:
        print("\n💡 Possible solutions:")
        print("1. Verify API key is correct and active")
        print("2. Check if your mem0 account needs verification")
        print("3. Try creating memories through mem0 web interface first")
        print("4. Contact mem0 support for API access verification")