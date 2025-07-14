#!/usr/bin/env python3
"""
Test script to manually trigger daily message tasks
Run this to test if the scheduled messaging system works
"""

import asyncio
import sys
import os

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from worker.tasks.daily_messages import send_morning_affirmations, send_daily_accountability_checkin, send_evening_gratitude

async def fix_test_subscription():
    """Fix WhatsApp ID format in test subscription"""
    try:
        from deps import get_supabase_client
        from services.supabase_client import SupabaseService
        
        print("🔧 Fixing WhatsApp ID format in test subscription...")
        
        # Initialize Supabase
        db = get_supabase_client()
        supabase_service = SupabaseService(db)
        
        # Get test subscription
        test_email = "test@positivitypush.com"
        result = db.table("subscribers").select("*").eq("email", test_email).execute()
        
        if not result.data:
            print(f"❌ No subscription found for {test_email}")
            return
        
        subscriber = result.data[0]
        current_wa_id = subscriber.get("wa_id")
        
        print(f"📱 Current WhatsApp ID: {current_wa_id}")
        
        if current_wa_id and current_wa_id.startswith("+"):
            # Remove the + prefix
            new_wa_id = current_wa_id[1:]  # Remove first character (+)
            
            # Update the record
            await supabase_service.update_subscription(
                subscriber["id"], 
                {"wa_id": new_wa_id}
            )
            
            print(f"✅ Updated WhatsApp ID from {current_wa_id} to {new_wa_id}")
        else:
            print(f"✅ WhatsApp ID format is already correct: {current_wa_id}")
        
    except Exception as e:
        print(f"❌ Error fixing WhatsApp ID: {e}")

async def test_scheduled_tasks():
    """Test all scheduled tasks manually"""
    
    print("🧪 Testing Scheduled Daily Tasks...")
    print("=" * 50)
    
    # First fix the WhatsApp ID format issue
    await fix_test_subscription()
    
    # Test morning affirmations
    print("\n📅 Testing Morning Affirmations (UTC timezone)...")
    try:
        result = send_morning_affirmations.delay('UTC')
        task_result = result.get(timeout=30)
        print(f"✅ Morning Affirmations Result: {task_result}")
    except Exception as e:
        print(f"❌ Morning Affirmations Failed: {e}")
    
    # Test accountability check-in
    print("\n📅 Testing Daily Accountability Check-in (UTC timezone)...")
    try:
        result = send_daily_accountability_checkin.delay('UTC')
        task_result = result.get(timeout=30)
        print(f"✅ Accountability Check-in Result: {task_result}")
    except Exception as e:
        print(f"❌ Accountability Check-in Failed: {e}")
    
    # Test evening gratitude
    print("\n📅 Testing Evening Gratitude (UTC timezone)...")
    try:
        result = send_evening_gratitude.delay('UTC')
        task_result = result.get(timeout=30)
        print(f"✅ Evening Gratitude Result: {task_result}")
    except Exception as e:
        print(f"❌ Evening Gratitude Failed: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Test Complete! Check your WhatsApp for messages.")

if __name__ == "__main__":
    asyncio.run(test_scheduled_tasks())