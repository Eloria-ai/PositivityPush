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
        
        # Keep WhatsApp ID as-is - no automatic modifications
        print(f"ℹ️ WhatsApp ID will be used as-is: {current_wa_id}")
        
    except Exception as e:
        print(f"❌ Error fixing WhatsApp ID: {e}")

async def test_scheduled_tasks():
    """Test all scheduled tasks manually"""
    
    print("🧪 Testing ALL Scheduled Daily Tasks...")
    print("=" * 60)
    
    # First fix the WhatsApp ID format issue
    await fix_test_subscription()
    
    print("\n" + "=" * 60)
    
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
    
    print("\n" + "=" * 60)
    print("🆕 TESTING NEW SCHEDULED TASKS...")
    print("=" * 60)
    
    # Test day planning
    print("\n📝 Testing Day Planning (UTC timezone)...")
    try:
        from worker.tasks.daily_messages import send_day_planning
        result = send_day_planning.delay('UTC')
        task_result = result.get(timeout=30)
        print(f"✅ Day Planning Result: {task_result}")
    except Exception as e:
        print(f"❌ Day Planning Failed: {e}")
    
    # Test midday affirmation
    print("\n☀️ Testing Midday Affirmation (UTC timezone)...")
    try:
        from worker.tasks.daily_messages import send_midday_affirmation
        result = send_midday_affirmation.delay('UTC')
        task_result = result.get(timeout=30)
        print(f"✅ Midday Affirmation Result: {task_result}")
    except Exception as e:
        print(f"❌ Midday Affirmation Failed: {e}")
    
    # Test evening affirmation
    print("\n🌙 Testing Evening Affirmation (UTC timezone)...")
    try:
        from worker.tasks.daily_messages import send_evening_affirmation
        result = send_evening_affirmation.delay('UTC')
        task_result = result.get(timeout=30)
        print(f"✅ Evening Affirmation Result: {task_result}")
    except Exception as e:
        print(f"❌ Evening Affirmation Failed: {e}")
    
    # Test weekly reflection
    print("\n🗓️ Testing Weekly Reflection (UTC timezone)...")
    try:
        from worker.tasks.daily_messages import send_weekly_reflection
        result = send_weekly_reflection.delay('UTC')
        task_result = result.get(timeout=30)
        print(f"✅ Weekly Reflection Result: {task_result}")
    except Exception as e:
        print(f"❌ Weekly Reflection Failed: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 COMPLETE TEST FINISHED! Check your WhatsApp for 6 new messages:")
    print("   🌅 Morning Affirmation")
    print("   📝 Day Planning") 
    print("   ☀️ Midday Affirmation")
    print("   💪 Accountability Check-in")
    print("   🌙 Evening Affirmation")
    print("   🙏 Evening Gratitude")
    print("   🗓️ Weekly Reflection")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_scheduled_tasks())
