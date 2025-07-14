#!/usr/bin/env python3
"""
Manual task trigger test to verify worker communication
Run this to test if tasks can be manually triggered
"""

import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(__file__))

def test_manual_task_trigger():
    """Test manual task triggering to verify worker communication"""
    
    print("🧪 Testing manual task trigger...")
    print("=" * 50)
    
    try:
        from worker.tasks.daily_messages import send_morning_affirmations
        print("✅ Successfully imported task")
        
        # Trigger the task manually
        print("📤 Triggering morning affirmations task for UTC timezone...")
        result = send_morning_affirmations.delay('UTC')
        print(f"✅ Task triggered successfully!")
        print(f"📋 Task ID: {result.id}")
        print(f"📍 Task Status: {result.status}")
        
        # Try to get the result (with timeout)
        print("⏳ Waiting for task completion (60 second timeout)...")
        try:
            task_result = result.get(timeout=60)
            print(f"🎉 Task completed successfully!")
            print(f"📊 Result: {task_result}")
        except Exception as e:
            print(f"⚠️ Task timeout or error: {e}")
            print("💡 Check worker logs for execution details")
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 This suggests task registration issues")
    except Exception as e:
        print(f"❌ Failed to trigger task: {e}")
        print("💡 This suggests worker communication issues")
    
    print("=" * 50)
    print("🔍 Check worker logs for task execution details")

if __name__ == "__main__":
    test_manual_task_trigger()