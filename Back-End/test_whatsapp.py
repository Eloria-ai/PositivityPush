#!/usr/bin/env python3
"""
Quick test script to verify WhatsApp message sending works
"""

import asyncio
import sys
import os

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__)))

from app.services.whatsapp_service import WhatsAppService

async def test_send_message():
    """Test sending a WhatsApp message directly"""
    
    # Your WhatsApp number (replace with actual number)
    wa_id = "+31657779475"
    
    # Test message
    test_message = "🧪 TEST MESSAGE: This is a direct test from the WhatsApp service. If you receive this, the Twilio integration is working!"
    
    print(f"Sending test message to {wa_id}")
    print(f"Message: {test_message}")
    
    try:
        # Initialize WhatsApp service
        whatsapp_service = WhatsAppService()
        
        # Send test message
        success = await whatsapp_service.send_message(wa_id, test_message)
        
        if success:
            print("✅ SUCCESS: Test message sent successfully!")
            print("Check your WhatsApp to see if you received it.")
        else:
            print("❌ FAILED: Test message failed to send")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    print("=== WhatsApp Direct Test ===")
    asyncio.run(test_send_message())