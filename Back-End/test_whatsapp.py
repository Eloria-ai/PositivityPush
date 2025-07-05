#!/usr/bin/env python3
"""
Test WhatsApp Service with Twilio
Quick test to verify WhatsApp message sending works
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.whatsapp_service import WhatsAppService

# Load environment variables
load_dotenv()

async def test_whatsapp_message():
    """Test sending a WhatsApp message"""
    
    # Initialize WhatsApp service
    whatsapp = WhatsAppService()
    
    print("🔧 Testing Twilio WhatsApp Integration...")
    print(f"Using Twilio number: {os.getenv('TWILIO_WHATSAPP_NUMBER')}")
    
    # For testing, we'll use the Twilio WhatsApp number as destination
    # In production, this would be the user's phone number from the database
    test_phone = "+12515128899"  # Using Twilio number for testing
    
    print("📱 Testing with Twilio number - update with your personal number for real testing")
    print(f"Current test number: {test_phone}")
    
    # Test message
    test_message = "🌟 Hello from Positivity Push! This is a test message from your AI coach. If you receive this, the WhatsApp integration is working perfectly! 🎉"
    
    print(f"📱 Sending test message to: {test_phone}")
    print(f"💬 Message: {test_message}")
    
    try:
        # Send the message
        success = await whatsapp.send_message(test_phone, test_message)
        
        if success:
            print("✅ SUCCESS! WhatsApp message sent successfully!")
            print("📱 Check your WhatsApp to confirm you received the message.")
        else:
            print("❌ FAILED: Could not send WhatsApp message")
            print("💡 Check your Twilio credentials and phone number format")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    # Check required environment variables
    required_vars = ["TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_WHATSAPP_NUMBER"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        print("Please check your .env file")
        sys.exit(1)
    
    print("🚀 Starting WhatsApp Test...")
    asyncio.run(test_whatsapp_message())