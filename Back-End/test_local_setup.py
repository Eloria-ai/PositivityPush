#!/usr/bin/env python3
"""
Local Development Testing Script for Positivity Push
Run this script to test the backend setup locally before deployment.
"""

import os
import sys
import subprocess
import importlib.util
from pathlib import Path

def check_python_version():
    """Check if Python version is adequate"""
    print("🐍 Checking Python version...")
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} is supported")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} is too old (need 3.8+)")
        return False

def check_dependencies():
    """Check if required dependencies are installed"""
    print("\n📦 Checking dependencies...")
    
    required_packages = [
        'fastapi', 'uvicorn', 'pydantic', 'dotenv', 
        'supabase', 'stripe', 'openai', 'celery', 'redis'
    ]
    
    missing_packages = []
    for package in required_packages:
        spec = importlib.util.find_spec(package)
        if spec is None:
            missing_packages.append(package)
            print(f"❌ {package} - NOT INSTALLED")
        else:
            print(f"✅ {package} - installed")
    
    if missing_packages:
        print(f"\n❌ Missing packages: {missing_packages}")
        print("Run: pip install -r requirements.txt")
        return False
    
    return True

def check_env_file():
    """Check if .env file exists with required variables"""
    print("\n🌍 Checking environment configuration...")
    
    env_file = Path('.env')
    if not env_file.exists():
        print("❌ .env file not found")
        print("Copy .env.local to .env and fill in your API keys")
        return False
    
    print("✅ .env file exists")
    
    # Check for required variables
    required_vars = [
        'ENVIRONMENT', 'SECRET_KEY', 'OPENAI_API_KEY', 
        'SUPABASE_URL', 'REDIS_URL'
    ]
    
    missing_vars = []
    with open('.env', 'r') as f:
        env_content = f.read()
    
    for var in required_vars:
        if var not in env_content or f"{var}=" not in env_content:
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {missing_vars}")
        return False
    
    print("✅ Required environment variables present")
    return True

def test_redis_connection():
    """Test Redis connection"""
    print("\n🔴 Testing Redis connection...")
    
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        print("✅ Redis connection successful")
        return True
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        print("Make sure Redis is running: redis-server")
        return False

def test_import_modules():
    """Test if our modules can be imported"""
    print("\n🔍 Testing module imports...")
    
    modules_to_test = [
        'app.main',
        'app.config',
        'app.services.ai_coach',
        'worker.celery_app'
    ]
    
    failed_imports = []
    for module in modules_to_test:
        try:
            importlib.import_module(module)
            print(f"✅ {module} - imported successfully")
        except Exception as e:
            failed_imports.append((module, str(e)))
            print(f"❌ {module} - import failed: {e}")
    
    if failed_imports:
        print(f"\n❌ Failed to import {len(failed_imports)} modules")
        return False
    
    return True

def run_basic_tests():
    """Run basic functionality tests"""
    print("\n🧪 Running basic tests...")
    
    try:
        # Test FastAPI app creation
        from app.main import app
        print("✅ FastAPI app created successfully")
        
        # Test config loading
        from app.config import settings
        print("✅ Configuration loaded successfully")
        
        # Test AI coach initialization
        from app.services.ai_coach import AICoachService
        coach = AICoachService()
        print("✅ AI Coach service initialized")
        
        return True
        
    except Exception as e:
        print(f"❌ Basic tests failed: {e}")
        return False

def main():
    """Main testing function"""
    print("🚀 Positivity Push - Local Development Testing")
    print("=" * 50)
    
    tests = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Environment File", check_env_file),
        ("Redis Connection", test_redis_connection),
        ("Module Imports", test_import_modules),
        ("Basic Tests", run_basic_tests)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name} failed")
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 LOCAL SETUP READY!")
        print("You can now start the backend services:")
        print("1. python -m app.main")
        print("2. celery -A worker.celery_app worker")
        print("3. celery -A worker.celery_app beat")
        return True
    else:
        print(f"\n❌ {total - passed} tests failed. Please fix the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)