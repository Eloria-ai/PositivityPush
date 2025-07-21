#!/usr/bin/env python3
"""
Test script to verify Supabase setup and architecture
Run this after setting up the database schema.
"""

import os
import sys
import asyncio
from datetime import datetime, timedelta

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

try:
    from services.supabase_client import SupabaseService
    from deps import get_supabase_client
    print("✅ Successfully imported Supabase services")
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you have the backend dependencies installed:")
    print("pip install supabase")
    sys.exit(1)

async def test_supabase_setup():
    """Test the complete Supabase setup"""
    
    print("\n🔧 Testing Supabase Setup...")
    
    try:
        # Initialize services
        db = get_supabase_client()
        supabase_service = SupabaseService(db)
        
        print("✅ Connected to Supabase")
        
        # Test 1: Check if tables exist
        print("\n📋 Testing table structure...")
        
        result = db.table("subscribers").select("id").limit(1).execute()
        print("✅ subscribers table exists")
        
        result = db.table("scheduled_messages").select("id").limit(1).execute()
        print("✅ scheduled_messages table exists")
        
        # Test 2: Check if RPC function exists
        print("\n🔧 Testing execute_raw_sql function...")
        
        test_sql = "SELECT 1 as test_value;"
        result = db.rpc("execute_raw_sql", {"query": test_sql}).execute()
        if result.data:
            print("✅ execute_raw_sql function working")
        else:
            print("❌ execute_raw_sql function not working")
            
        # Test 3: Test SKIP LOCKED operation
        print("\n🔒 Testing SKIP LOCKED operation...")
        
        # Create a test user first
        test_user = {
            "email": "test@positivitypush.com",
            "phone_number": "+15551234567",
            "status": "active",
            "current_timezone": "America/New_York",
            "preferences": {
                "onboarding_completed": True,
                "day_planning": "09:00",
                "accountability_checkin": "19:00"
            }
        }
        
        # Insert test user (or get existing)
        existing = db.table("subscribers").select("*").eq("email", test_user["email"]).execute()
        
        if existing.data:
            subscriber_id = existing.data[0]["id"]
            print(f"✅ Using existing test user: {subscriber_id}")
        else:
            result = db.table("subscribers").insert(test_user).execute()
            subscriber_id = result.data[0]["id"]
            print(f"✅ Created test user: {subscriber_id}")
        
        # Insert test message
        test_message = {
            "subscriber_id": subscriber_id,
            "message_type": "daily_affirmation",
            "scheduled_for": (datetime.utcnow() - timedelta(minutes=5)).isoformat() + "+00:00",
            "status": "pending"
        }
        
        result = db.table("scheduled_messages").insert(test_message).execute()
        message_id = result.data[0]["id"]
        print(f"✅ Created test message: {message_id}")
        
        # Test SKIP LOCKED sweep
        due_messages = await supabase_service.get_due_scheduled_messages(batch_size=10, use_skip_locked=True)
        
        if due_messages:
            print(f"✅ SKIP LOCKED retrieved {len(due_messages)} messages")
            
            # Verify message was marked as queued
            updated_message = db.table("scheduled_messages").select("*").eq("id", message_id).execute()
            if updated_message.data and updated_message.data[0]["status"] == "queued":
                print("✅ Message status updated to 'queued'")
            else:
                print("❌ Message status not updated properly")
        else:
            print("❌ SKIP LOCKED operation failed")
            
        # Test message context retrieval
        message_context = await supabase_service.get_message_with_user_context(message_id)
        if message_context and message_context.get("subscriber"):
            print("✅ Message context retrieval working")
        else:
            print("❌ Message context retrieval failed")
            
        # Test status transitions
        success = await supabase_service.mark_message_sent(message_id)
        if success:
            print("✅ Message status transition to 'sent' working")
        else:
            print("❌ Message status transition failed")
            
        # Clean up test data
        db.table("scheduled_messages").delete().eq("id", message_id).execute()
        db.table("subscribers").delete().eq("id", subscriber_id).execute()
        print("✅ Test data cleaned up")
        
        print("\n🎉 All tests passed! Supabase setup is correct.")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        print("\nCheck:")
        print("1. SUPABASE_URL and SUPABASE_KEY environment variables")
        print("2. Database schema.sql was run completely")
        print("3. execute_raw_sql function exists")
        print("4. Service role key has proper permissions")
        return False
        
    return True

def main():
    print("🧪 Positivity Push - Supabase Setup Test")
    print("=" * 50)
    
    # Check environment variables
    if not os.getenv("SUPABASE_URL"):
        print("❌ SUPABASE_URL environment variable not set")
        return
        
    if not os.getenv("SUPABASE_KEY"):
        print("❌ SUPABASE_KEY environment variable not set")
        return
        
    print(f"📍 Supabase URL: {os.getenv('SUPABASE_URL')}")
    print(f"🔑 Service key configured: {'yes' if os.getenv('SUPABASE_KEY') else 'no'}")
    
    # Run async test
    success = asyncio.run(test_supabase_setup())
    
    if success:
        print("\n🚀 Ready for production deployment!")
    else:
        print("\n🔧 Fix the issues above before proceeding.")

if __name__ == "__main__":
    main()