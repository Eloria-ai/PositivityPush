"""
Test script for Positivity Push Background Workers
Tests Celery tasks, Redis connection, and scheduled messaging.
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'worker'))

# Load environment variables
load_dotenv()

def test_redis_connection():
    """Test Redis connection for Celery"""
    print("🔴 Testing Redis connection...")
    
    try:
        import redis
        
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        r = redis.from_url(redis_url)
        
        # Test connection
        r.ping()
        print("✅ Redis connection successful")
        
        # Test basic operations
        r.set("test_key", "test_value", ex=10)
        value = r.get("test_key")
        
        if value == b"test_value":
            print("✅ Redis read/write operations working")
            return True
        else:
            print("❌ Redis read/write failed")
            return False
            
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        return False

def test_celery_import():
    """Test that Celery tasks can be imported"""
    print("\n📦 Testing Celery task imports...")
    
    try:
        from worker.celery_app import celery_app
        print("✅ Celery app imported successfully")
        
        # Test task imports
        from worker.tasks.daily_messages import send_morning_affirmations, send_evening_gratitude
        print("✅ Daily message tasks imported")
        
        from worker.tasks.weekly_reports import send_weekly_progress_reports
        print("✅ Weekly report tasks imported")
        
        from worker.tasks.email_notifications import send_welcome_email, send_activation_reminders
        print("✅ Email notification tasks imported")
        
        return True
        
    except Exception as e:
        print(f"❌ Celery import failed: {e}")
        return False

def test_celery_worker_connection():
    """Test connection to Celery worker"""
    print("\n👷 Testing Celery worker connection...")
    
    try:
        from worker.celery_app import celery_app
        
        # Check if workers are active
        inspect = celery_app.control.inspect()
        active_workers = inspect.active()
        
        if active_workers:
            print(f"✅ Found {len(active_workers)} active Celery workers")
            for worker, tasks in active_workers.items():
                print(f"  - Worker: {worker}, Active tasks: {len(tasks)}")
            return True
        else:
            print("⚠️ No active Celery workers found")
            print("   Start worker with: celery -A worker.celery_app worker --loglevel=info")
            return False
            
    except Exception as e:
        print(f"❌ Celery worker connection failed: {e}")
        return False

def test_task_execution():
    """Test executing a simple Celery task"""
    print("\n🚀 Testing task execution...")
    
    try:
        from worker.celery_app import celery_app
        from worker.tasks.email_notifications import send_welcome_email
        
        # Test data
        test_subscription = {
            "email": "test@example.com",
            "plan_type": "3_month",
            "amount_total": 7500,
            "stripe_session_id": "test_session_123"
        }
        
        # Send async task
        result = send_welcome_email.delay(test_subscription)
        
        print(f"✅ Task queued successfully. Task ID: {result.id}")
        print("   Note: Check worker logs to see if task executes")
        
        return True
        
    except Exception as e:
        print(f"❌ Task execution test failed: {e}")
        return False

def test_scheduled_tasks():
    """Test scheduled task configuration"""
    print("\n⏰ Testing scheduled task configuration...")
    
    try:
        from worker.celery_app import celery_app
        
        beat_schedule = celery_app.conf.beat_schedule
        
        print(f"✅ Found {len(beat_schedule)} scheduled tasks:")
        for task_name, config in beat_schedule.items():
            schedule = config['schedule']
            task = config['task']
            print(f"  - {task_name}: {task}")
            print(f"    Schedule: {schedule}")
        
        return True
        
    except Exception as e:
        print(f"❌ Scheduled tasks test failed: {e}")
        return False

def test_environment_variables():
    """Test required environment variables for workers"""
    print("\n🌍 Testing environment variables...")
    
    required_vars = [
        "REDIS_URL",
        "OPENAI_API_KEY",
        "SUPABASE_URL",
        "SUPABASE_SERVICE_KEY"
    ]
    
    optional_vars = [
        "MEM0_API_KEY",
        "SENDGRID_API_KEY", 
        "WA_TOKEN",
        "STRIPE_SECRET_KEY"
    ]
    
    missing_required = []
    missing_optional = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_required.append(var)
        else:
            print(f"✅ {var} is set")
    
    for var in optional_vars:
        if not os.getenv(var):
            missing_optional.append(var)
        else:
            print(f"✅ {var} is set")
    
    if missing_required:
        print(f"❌ Missing required variables: {missing_required}")
        return False
    
    if missing_optional:
        print(f"⚠️ Missing optional variables: {missing_optional}")
        print("   Some features may not work without these")
    
    return True

async def test_ai_coach_integration():
    """Test AI Coach integration for background tasks"""
    print("\n🧠 Testing AI Coach integration...")
    
    try:
        # Import AI services
        from services.ai_coach import AICoachService
        from services.supabase_client import SupabaseService
        from deps import get_supabase_client
        
        # Test AI Coach
        ai_coach = AICoachService()
        
        test_context = {
            "id": "test-worker-user",
            "email": "worker-test@example.com", 
            "plan_type": "3_month"
        }
        
        # Test affirmation generation
        affirmation = await ai_coach.generate_daily_affirmation("test-worker-user", test_context)
        print(f"✅ Generated affirmation: {affirmation[:50]}...")
        
        # Test gratitude prompt
        gratitude = await ai_coach.generate_gratitude_prompt("test-worker-user", test_context)
        print(f"✅ Generated gratitude prompt: {gratitude[:50]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ AI Coach integration test failed: {e}")
        return False

def show_worker_commands():
    """Show commands to start workers"""
    print("\n📋 Commands to start Celery workers:")
    print("=" * 50)
    
    print("1. Start main worker:")
    print("   celery -A worker.celery_app worker --loglevel=info")
    
    print("\n2. Start beat scheduler (for periodic tasks):")
    print("   celery -A worker.celery_app beat --loglevel=info")
    
    print("\n3. Start both worker and beat:")
    print("   celery -A worker.celery_app worker --beat --loglevel=info")
    
    print("\n4. Start with specific queues:")
    print("   celery -A worker.celery_app worker -Q daily_messages,email_notifications --loglevel=info")
    
    print("\n5. Monitor tasks:")
    print("   celery -A worker.celery_app flower")
    
    print("\n6. Purge all tasks:")
    print("   celery -A worker.celery_app purge")

async def run_all_tests():
    """Run all worker tests"""
    print("🔄 Starting Positivity Push Worker Tests")
    print("=" * 50)
    
    tests = [
        ("Environment Variables", test_environment_variables),
        ("Redis Connection", test_redis_connection),
        ("Celery Imports", test_celery_import),
        ("Celery Worker Connection", test_celery_worker_connection),
        ("Scheduled Tasks Config", test_scheduled_tasks),
        ("Task Execution", test_task_execution),
        ("AI Coach Integration", test_ai_coach_integration),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running: {test_name}")
        print("-" * 30)
        
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("🎯 WORKER TESTS SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n📊 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All worker tests passed! Your background system is ready!")
    elif passed >= total * 0.7:
        print("⚠️ Most tests passed. Check failed tests for worker setup.")
    else:
        print("❌ Multiple failures. Check Redis, Celery, and environment setup.")
    
    show_worker_commands()

if __name__ == "__main__":
    asyncio.run(run_all_tests())