#!/usr/bin/env python3
"""
Create Test Subscription for WhatsApp Testing
Creates a real subscription entry in Supabase for testing AI coach conversations
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.supabase_client import SupabaseService
from app.deps import get_supabase_client

# Load environment variables
load_dotenv()

async def create_test_subscription():
    """Create a test subscription for WhatsApp testing"""
    
    print("🧪 Creating test subscription for AI coach testing...")
    
    # Your WhatsApp number (replace with the number you're testing from)
    test_phone = input("Enter your WhatsApp number (with country code, e.g., +1234567890): ")
    
    if not test_phone.startswith("+"):
        print("❌ Please include country code (e.g., +1234567890)")
        return
    
    try:
        # Get Supabase client
        supabase_client = get_supabase_client()
        supabase_service = SupabaseService(supabase_client)
        
        # Test subscription data
        subscription_data = {
            "phone_number": test_phone,
            "email": "test@positivitypush.com",
            "wa_id": test_phone,
            "stripe_customer_id": "cus_test_123456",
            "stripe_session_id": "cs_test_a10dkNGMKTWudQBdZ0p0wK7jl1T9FAa1poeJbbIbDwbn9xGzOVDIhXc5Tz",
            "plan_type": "3_month",
            "status": "active",
            "personal_goals": "Test AI coaching features",
            "communication_style": "friendly",
            "active_challenges": "Testing the system"
        }
        
        print(f"📱 Creating subscription for: {test_phone}")
        print(f"📊 Plan: {subscription_data['plan_type']}")
        print(f"🎯 Status: {subscription_data['status']}")
        
        # Insert subscription
        result = await supabase_service.create_subscription(subscription_data)
        
        if result:
            print("✅ SUCCESS! Test subscription created!")
            print(f"🆔 Subscription ID: {result.get('id')}")
            print("\n🎉 You can now chat with your AI coach!")
            print("📱 Send any message to the WhatsApp sandbox number to start coaching")
            print("\n💬 Try messages like:")
            print("  • Hello coach, how are you today?")
            print("  • I need motivation for my goals")
            print("  • What should I focus on this week?")
        else:
            print("❌ Failed to create test subscription")
            
    except Exception as e:
        print(f"❌ Error creating test subscription: {e}")

if __name__ == "__main__":
    print("🚀 Starting Test Subscription Creation...")
    asyncio.run(create_test_subscription())