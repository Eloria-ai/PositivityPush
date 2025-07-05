#!/usr/bin/env python3
"""
Check Twilio WhatsApp Sandbox Status
Verify if the number is properly configured and what the sandbox requirements are
"""

import asyncio
import os
import sys
import httpx
import base64
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def check_twilio_sandbox():
    """Check Twilio WhatsApp sandbox configuration"""
    
    print("🔧 Checking Twilio WhatsApp Sandbox Configuration...")
    
    # Get credentials
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN") 
    whatsapp_number = os.getenv("TWILIO_WHATSAPP_NUMBER")
    
    print(f"WhatsApp Number: {whatsapp_number}")
    
    try:
        # Create Basic Auth header
        credentials = f"{account_sid}:{auth_token}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/json"
        }
        
        base_url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}"
        
        async with httpx.AsyncClient() as client:
            # Check phone numbers associated with account
            print("\n📱 Checking available WhatsApp numbers...")
            
            # Check incoming phone numbers
            numbers_response = await client.get(
                f"{base_url}/IncomingPhoneNumbers.json",
                headers=headers
            )
            
            if numbers_response.status_code == 200:
                numbers_data = numbers_response.json()
                phone_numbers = numbers_data.get("incoming_phone_numbers", [])
                
                print(f"Found {len(phone_numbers)} phone numbers in account:")
                for number in phone_numbers:
                    print(f"  - {number.get('phone_number')}: {number.get('friendly_name', 'No name')}")
                    print(f"    Capabilities: SMS={number.get('capabilities', {}).get('sms')}, "
                          f"Voice={number.get('capabilities', {}).get('voice')}")
                
                # Check if our WhatsApp number is in the list
                our_number_found = any(num.get('phone_number') == whatsapp_number for num in phone_numbers)
                
                if our_number_found:
                    print(f"✅ WhatsApp number {whatsapp_number} found in account!")
                else:
                    print(f"⚠️  WhatsApp number {whatsapp_number} NOT found in regular phone numbers")
                    print("This might be a sandbox number - checking sandbox status...")
            
            # Check for WhatsApp sandbox specifically
            print("\n🏖️  Checking WhatsApp Sandbox status...")
            
            # Try to get sandbox status (this endpoint might not exist, but let's try)
            sandbox_response = await client.get(
                f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Sandbox/WhatsApp.json",
                headers=headers
            )
            
            if sandbox_response.status_code == 200:
                sandbox_data = sandbox_response.json()
                print("✅ WhatsApp Sandbox found:")
                print(f"  Phone Number: {sandbox_data.get('phone_number', 'Not found')}")
                print(f"  Status: {sandbox_data.get('status', 'Unknown')}")
            else:
                print(f"⚠️  Sandbox endpoint returned: {sandbox_response.status_code}")
                
            # Check recent messages to see if sandbox is working
            print("\n📨 Checking recent messages...")
            messages_response = await client.get(
                f"{base_url}/Messages.json?PageSize=5",
                headers=headers
            )
            
            if messages_response.status_code == 200:
                messages_data = messages_response.json()
                messages = messages_data.get("messages", [])
                
                print(f"Found {len(messages)} recent messages:")
                for msg in messages:
                    print(f"  - From: {msg.get('from')} To: {msg.get('to')}")
                    print(f"    Status: {msg.get('status')} Direction: {msg.get('direction')}")
                    print(f"    Body: {msg.get('body', '')[:50]}...")
                    
    except Exception as e:
        print(f"❌ Error checking Twilio sandbox: {e}")

if __name__ == "__main__":
    print("🚀 Starting Twilio Sandbox Check...")
    asyncio.run(check_twilio_sandbox())