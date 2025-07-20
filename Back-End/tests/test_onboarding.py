"""
Test the onboarding system locally
"""

import asyncio
import sys
import os

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.supabase_client import SupabaseService
from app.services.onboarding_service import OnboardingService
from app.deps import get_supabase_client

async def test_onboarding():
    """Test the onboarding flow"""
    
    try:
        print("🧪 Testing Onboarding System...")
        
        # Initialize services
        db = get_supabase_client()
        supabase_service = SupabaseService(db)
        onboarding_service = OnboardingService(supabase_service)
        
        # Get active user for testing
        active_users = await supabase_service.get_active_subscribers()
        
        if not active_users:
            print("❌ No active users found for testing")
            return
            
        user = active_users[0]
        user_id = user["id"]
        wa_id = user.get("wa_id", "+31657779475")  # Fallback to your number
        
        print(f"👤 Testing with user: {user['email']} (WA: {wa_id})")
        
        # Check current onboarding status
        preferences = await supabase_service.get_user_preferences(user_id)
        onboarding_completed = preferences.get("onboarding_completed", False)
        
        print(f"📊 Current onboarding status: {onboarding_completed}")
        
        if onboarding_completed:
            # Reset onboarding for testing
            print("🔄 Resetting onboarding status for testing...")
            await supabase_service.set_preference_value(user_id, "onboarding_completed", False)
        
        # Test starting onboarding using Celery task
        print("🚀 Starting onboarding...")
        from worker.tasks.onboarding_tasks import send_onboarding_welcome_flow
        task = send_onboarding_welcome_flow.delay(user_id, wa_id)
        
        print("✅ Onboarding task enqueued! Check your WhatsApp for the welcome message and first question.")
        print("💬 You can now respond to test the interactive flow!")
        print(f"📋 Task ID: {task.id}")
        
        # Show current preferences
        updated_preferences = await supabase_service.get_user_preferences(user_id)
        print(f"📝 Current preferences: {updated_preferences}")
        
    except Exception as e:
        print(f"❌ Error testing onboarding: {e}")

if __name__ == "__main__":
    asyncio.run(test_onboarding())