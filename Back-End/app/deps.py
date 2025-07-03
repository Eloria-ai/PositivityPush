"""
Dependency injection for Positivity Push API
Common dependencies and database connections.
"""

from typing import Generator
from fastapi import Depends, HTTPException, status
from supabase import create_client, Client
import stripe
import openai
from app.config import settings

# Configure external services
stripe.api_key = settings.STRIPE_SECRET_KEY
openai.api_key = settings.OPENAI_API_KEY

def get_supabase_client() -> Client:
    """Get Supabase client instance"""
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Supabase configuration missing"
        )
    
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)

def get_stripe_client():
    """Get configured Stripe client"""
    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Stripe configuration missing"
        )
    return stripe

def get_openai_client():
    """Get configured OpenAI client"""
    if not settings.OPENAI_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OpenAI configuration missing"
        )
    return openai

# Database dependency
def get_db() -> Generator[Client, None, None]:
    """Database dependency for route injection"""
    try:
        db = get_supabase_client()
        yield db
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database connection failed: {str(e)}"
        )