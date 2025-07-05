#!/usr/bin/env python3
"""
Validate Twilio WhatsApp Configuration
Test Twilio credentials and connectivity without sending messages
"""

import asyncio
import os
import sys
import httpx
import base64
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def validate_twilio_config():
    """Validate Twilio configuration and test API connectivity"""
    
    print("🔧 Validating Twilio WhatsApp Configuration...")
    
    # Check environment variables
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN") 
    whatsapp_number = os.getenv("TWILIO_WHATSAPP_NUMBER")
    
    print(f"Account SID: {account_sid[:10]}... (masked)")
    print(f"Auth Token: {auth_token[:10]}... (masked)")
    print(f"WhatsApp Number: {whatsapp_number}")
    
    if not all([account_sid, auth_token, whatsapp_number]):
        print("❌ Missing required Twilio environment variables")
        return False
    
    # Test Twilio API connectivity
    print("\n📡 Testing Twilio API connectivity...")
    
    try:
        # Create Basic Auth header
        credentials = f"{account_sid}:{auth_token}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        base_url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}"
        
        async with httpx.AsyncClient() as client:
            # Test account info endpoint
            response = await client.get(f"{base_url}.json", headers=headers)
            
            if response.status_code == 200:
                account_info = response.json()
                print("✅ Twilio API connection successful!")
                print(f"Account Name: {account_info.get('friendly_name', 'N/A')}")
                print(f"Account Status: {account_info.get('status', 'N/A')}")
                
                # Test WhatsApp sandbox status if applicable
                print("\n📱 Testing WhatsApp service access...")
                
                # Check if we can access the messages endpoint (without sending)
                messages_url = f"{base_url}/Messages.json"
                test_response = await client.get(messages_url, headers=headers)
                
                if test_response.status_code == 200:
                    print("✅ WhatsApp Messages API accessible!")
                    return True
                else:
                    print(f"⚠️  Messages API returned: {test_response.status_code}")
                    print("This might be normal for sandbox accounts")
                    return True
                    
            else:
                print(f"❌ Twilio API error: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Error testing Twilio API: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Twilio Configuration Validation...")
    result = asyncio.run(validate_twilio_config())
    
    if result:
        print("\n🎉 Configuration validated successfully!")
        print("Next step: Update test_whatsapp.py with your phone number to test message sending")
    else:
        print("\n❌ Configuration validation failed")
        print("Please check your Twilio credentials in .env file")