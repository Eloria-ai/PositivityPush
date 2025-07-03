"""
Production Validation Script for Positivity Push
Validates that all systems are ready for production deployment.
"""

import asyncio
import os
import sys
import requests
import json
from datetime import datetime
from typing import Dict, List, Tuple
from dotenv import load_dotenv

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from config import settings

# Load environment variables
load_dotenv()

class ProductionValidator:
    """Validates production readiness"""
    
    def __init__(self):
        self.results = []
        self.errors = []
        self.warnings = []
    
    def validate_environment_variables(self) -> bool:
        """Validate all required environment variables"""
        print("🌍 Validating environment variables...")
        
        required_vars = {
            "ENVIRONMENT": "production",
            "SECRET_KEY": None,
            "SUPABASE_URL": None,
            "SUPABASE_SERVICE_KEY": None,
            "STRIPE_SECRET_KEY": None,
            "STRIPE_WEBHOOK_SECRET": None,
            "OPENAI_API_KEY": None,
            "WA_TOKEN": None,
            "WA_PHONE_ID": None,
            "REDIS_URL": None,
            "SENDGRID_API_KEY": None,
            "FROM_EMAIL": None,
            "FRONTEND_URL": None
        }
        
        optional_vars = {
            "MEM0_API_KEY": "Memory service",
            "SENTRY_DSN": "Error tracking",
            "WA_BUSINESS_NUMBER": "WhatsApp display number"
        }
        
        missing_required = []
        missing_optional = []
        insecure_values = []
        
        for var, expected in required_vars.items():
            value = os.getenv(var)
            if not value:
                missing_required.append(var)
            else:
                # Check for insecure default values
                if var == "SECRET_KEY" and "change-in-production" in value:
                    insecure_values.append(var)
                elif var == "ENVIRONMENT" and expected and value != expected:
                    self.warnings.append(f"ENVIRONMENT is '{value}', expected '{expected}'")
                print(f"✅ {var} is set")
        
        for var, description in optional_vars.items():
            if not os.getenv(var):
                missing_optional.append(f"{var} ({description})")
            else:
                print(f"✅ {var} is set")
        
        if missing_required:
            self.errors.append(f"Missing required variables: {missing_required}")
            return False
        
        if insecure_values:
            self.errors.append(f"Insecure default values: {insecure_values}")
            return False
        
        if missing_optional:
            self.warnings.append(f"Missing optional variables: {missing_optional}")
        
        return True
    
    def validate_external_services(self) -> bool:
        """Validate external service connectivity"""
        print("\n🔌 Validating external services...")
        
        success = True
        
        # Test Redis
        try:
            import redis
            redis_url = os.getenv("REDIS_URL")
            if redis_url:
                r = redis.from_url(redis_url)
                r.ping()
                print("✅ Redis connection successful")
            else:
                self.errors.append("Redis URL not configured")
                success = False
        except Exception as e:
            self.errors.append(f"Redis connection failed: {e}")
            success = False
        
        # Test Supabase
        try:
            from deps import get_supabase_client
            db = get_supabase_client()
            # Simple test query
            result = db.table("subscribers").select("count", count="exact").limit(1).execute()
            print("✅ Supabase connection successful")
        except Exception as e:
            self.errors.append(f"Supabase connection failed: {e}")
            success = False
        
        # Test OpenAI
        try:
            import openai
            client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            # Simple test request
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5
            )
            print("✅ OpenAI API connection successful")
        except Exception as e:
            self.errors.append(f"OpenAI API connection failed: {e}")
            success = False
        
        # Test SendGrid (optional)
        sendgrid_key = os.getenv("SENDGRID_API_KEY")
        if sendgrid_key:
            try:
                import sendgrid
                sg = sendgrid.SendGridAPIClient(api_key=sendgrid_key)
                # Test API key validity
                response = sg.client.user.account.get()
                if response.status_code == 200:
                    print("✅ SendGrid API connection successful")
                else:
                    self.warnings.append("SendGrid API key may be invalid")
            except Exception as e:
                self.warnings.append(f"SendGrid validation failed: {e}")
        
        return success
    
    def validate_security_configuration(self) -> bool:
        """Validate security settings"""
        print("\n🔒 Validating security configuration...")
        
        security_checks = []
        
        # Check SECRET_KEY strength
        secret_key = os.getenv("SECRET_KEY", "")
        if len(secret_key) < 32:
            self.errors.append("SECRET_KEY is too short (minimum 32 characters)")
            security_checks.append(False)
        else:
            print("✅ SECRET_KEY length is adequate")
            security_checks.append(True)
        
        # Check HTTPS URLs
        frontend_url = os.getenv("FRONTEND_URL", "")
        if frontend_url and not frontend_url.startswith("https://"):
            self.warnings.append("FRONTEND_URL should use HTTPS in production")
        else:
            print("✅ Frontend URL uses HTTPS")
        
        # Check environment setting
        if settings.ENVIRONMENT != "production":
            self.warnings.append(f"ENVIRONMENT is '{settings.ENVIRONMENT}', should be 'production'")
        else:
            print("✅ Environment set to production")
        
        return all(security_checks)
    
    def validate_file_structure(self) -> bool:
        """Validate required files exist"""
        print("\n📁 Validating file structure...")
        
        required_files = [
            "requirements.txt",
            "Dockerfile",
            "docker-compose.yml",
            "railway.json",
            "app/main.py",
            "app/config.py",
            "worker/celery_app.py",
            "database/schema.sql"
        ]
        
        missing_files = []
        for file_path in required_files:
            if os.path.exists(file_path):
                print(f"✅ {file_path} exists")
            else:
                missing_files.append(file_path)
        
        if missing_files:
            self.errors.append(f"Missing required files: {missing_files}")
            return False
        
        return True
    
    def validate_database_schema(self) -> bool:
        """Validate database schema is up to date"""
        print("\n🗄️ Validating database schema...")
        
        try:
            from deps import get_supabase_client
            db = get_supabase_client()
            
            # Check if required tables exist
            required_tables = ["subscribers", "conversations", "user_progress"]
            
            for table in required_tables:
                try:
                    result = db.table(table).select("*").limit(1).execute()
                    print(f"✅ Table '{table}' exists and is accessible")
                except Exception as e:
                    self.errors.append(f"Table '{table}' validation failed: {e}")
                    return False
            
            return True
            
        except Exception as e:
            self.errors.append(f"Database schema validation failed: {e}")
            return False
    
    def validate_webhook_endpoints(self) -> bool:
        """Validate webhook endpoint configuration"""
        print("\n🪝 Validating webhook configuration...")
        
        webhook_config = {
            "Stripe webhook secret": os.getenv("STRIPE_WEBHOOK_SECRET"),
            "WhatsApp verify token": os.getenv("WA_WEBHOOK_VERIFY_TOKEN"),
            "WhatsApp access token": os.getenv("WA_TOKEN")
        }
        
        missing_config = []
        for config_name, value in webhook_config.items():
            if value:
                print(f"✅ {config_name} is configured")
            else:
                missing_config.append(config_name)
        
        if missing_config:
            self.errors.append(f"Missing webhook configuration: {missing_config}")
            return False
        
        return True
    
    def validate_task_scheduling(self) -> bool:
        """Validate Celery task configuration"""
        print("\n⏰ Validating task scheduling...")
        
        try:
            from worker.celery_app import celery_app
            
            # Check if beat schedule is configured
            beat_schedule = celery_app.conf.beat_schedule
            
            required_tasks = [
                "send-morning-affirmations-utc",
                "send-evening-gratitude-utc",
                "send-weekly-progress-reports"
            ]
            
            missing_tasks = []
            for task in required_tasks:
                if task in beat_schedule:
                    print(f"✅ Task '{task}' is scheduled")
                else:
                    missing_tasks.append(task)
            
            if missing_tasks:
                self.errors.append(f"Missing scheduled tasks: {missing_tasks}")
                return False
            
            return True
            
        except Exception as e:
            self.errors.append(f"Task scheduling validation failed: {e}")
            return False
    
    def validate_logging_configuration(self) -> bool:
        """Validate logging is properly configured"""
        print("\n📝 Validating logging configuration...")
        
        try:
            # Check if logs directory exists or can be created
            logs_dir = os.path.join(os.getcwd(), 'logs')
            os.makedirs(logs_dir, exist_ok=True)
            
            # Test logging functionality
            from logging_config import setup_logging, get_logger
            setup_logging()
            
            logger = get_logger("production.validation")
            logger.info("Testing production logging configuration")
            
            print("✅ Logging configuration successful")
            return True
            
        except Exception as e:
            self.errors.append(f"Logging configuration failed: {e}")
            return False
    
    async def run_all_validations(self) -> Dict:
        """Run all production validations"""
        print("🚀 Starting Production Readiness Validation")
        print("=" * 60)
        
        validations = [
            ("Environment Variables", self.validate_environment_variables),
            ("External Services", self.validate_external_services),
            ("Security Configuration", self.validate_security_configuration),
            ("File Structure", self.validate_file_structure),
            ("Database Schema", self.validate_database_schema),
            ("Webhook Configuration", self.validate_webhook_endpoints),
            ("Task Scheduling", self.validate_task_scheduling),
            ("Logging Configuration", self.validate_logging_configuration)
        ]
        
        passed = 0
        total = len(validations)
        
        for validation_name, validation_func in validations:
            try:
                if validation_func():
                    passed += 1
                    self.results.append((validation_name, True))
                else:
                    self.results.append((validation_name, False))
            except Exception as e:
                self.errors.append(f"Validation '{validation_name}' crashed: {e}")
                self.results.append((validation_name, False))
        
        # Summary
        print("\n" + "=" * 60)
        print("🎯 PRODUCTION VALIDATION SUMMARY")
        print("=" * 60)
        
        for validation_name, passed_check in self.results:
            status = "✅ PASS" if passed_check else "❌ FAIL"
            print(f"{status} {validation_name}")
        
        print(f"\n📊 Overall: {passed}/{total} validations passed")
        
        # Show errors
        if self.errors:
            print("\n❌ ERRORS (must fix before deployment):")
            for error in self.errors:
                print(f"  • {error}")
        
        # Show warnings
        if self.warnings:
            print("\n⚠️ WARNINGS (recommended to fix):")
            for warning in self.warnings:
                print(f"  • {warning}")
        
        # Final assessment
        if passed == total and not self.errors:
            print("\n🎉 PRODUCTION READY!")
            print("Your Positivity Push backend is ready for deployment!")
            ready = True
        elif passed >= total * 0.8 and not self.errors:
            print("\n⚠️ MOSTLY READY")
            print("Address warnings before deployment for best results.")
            ready = True
        else:
            print("\n❌ NOT READY FOR PRODUCTION")
            print("Fix critical errors before deploying.")
            ready = False
        
        return {
            "ready": ready,
            "passed": passed,
            "total": total,
            "errors": self.errors,
            "warnings": self.warnings,
            "timestamp": datetime.utcnow().isoformat()
        }

async def main():
    """Main validation function"""
    validator = ProductionValidator()
    result = await validator.run_all_validations()
    
    # Exit with appropriate code
    sys.exit(0 if result["ready"] else 1)

if __name__ == "__main__":
    asyncio.run(main())