"""
Configuration settings for Positivity Push API
Manages environment variables and application settings.
"""

import os
from typing import List
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application Settings
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    
    # CORS Settings
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",  # Local frontend
        "https://positivity-push.vercel.app",  # Production frontend
        "https://positivity-push-gamma.vercel.app",  # Alternative production
    ]
    
    # Database Settings (Supabase)
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY", "")
    SUPABASE_SERVICE_KEY: str = os.getenv("SUPABASE_SERVICE_KEY", "")
    
    # Stripe Settings
    STRIPE_SECRET_KEY: str = os.getenv("STRIPE_SECRET_KEY", "")
    STRIPE_WEBHOOK_SECRET: str = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    STRIPE_PUBLISHABLE_KEY: str = os.getenv("STRIPE_PUBLISHABLE_KEY", "")
    
    # WhatsApp Business API Settings
    WA_TOKEN: str = os.getenv("WA_TOKEN", "")
    WA_PHONE_ID: str = os.getenv("WA_PHONE_ID", "")
    WA_BUSINESS_NUMBER: str = os.getenv("WA_BUSINESS_NUMBER", "1234567890")
    WA_WEBHOOK_VERIFY_TOKEN: str = os.getenv("WA_WEBHOOK_VERIFY_TOKEN", "")
    
    # OpenAI Settings
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = "gpt-4o-mini"
    
    # mem0 Settings
    MEM0_API_KEY: str = os.getenv("MEM0_API_KEY", "")
    MEM0_URL: str = os.getenv("MEM0_URL", "")
    
    # Redis/Celery Settings
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", REDIS_URL)
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", REDIS_URL)
    
    # Email Settings
    SENDGRID_API_KEY: str = os.getenv("SENDGRID_API_KEY", "")
    FROM_EMAIL: str = os.getenv("FROM_EMAIL", "hello@positivitypush.com")
    
    # Frontend URLs
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "https://positivity-push.vercel.app")
    SUCCESS_PAGE_URL: str = f"{FRONTEND_URL}/success"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Create settings instance
settings = Settings()

# Validation function to check required settings
def validate_required_settings():
    """Validate that all required environment variables are set"""
    required_for_production = [
        "SUPABASE_URL",
        "SUPABASE_SERVICE_KEY", 
        "STRIPE_SECRET_KEY",
        "STRIPE_WEBHOOK_SECRET",
        "WA_TOKEN",
        "WA_PHONE_ID", 
        "OPENAI_API_KEY"
    ]
    
    missing = []
    if settings.ENVIRONMENT == "production":
        for setting in required_for_production:
            if not getattr(settings, setting):
                missing.append(setting)
    
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

# Run validation on import
if settings.ENVIRONMENT == "production":
    validate_required_settings()