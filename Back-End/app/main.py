"""
Positivity Push - FastAPI Backend
Main application entry point for WhatsApp-based AI coaching service.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
from dotenv import load_dotenv

from app.routers import stripe_webhook, whatsapp_webhook
from app.config import settings

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="Positivity Push API",
    description="WhatsApp-based AI coaching service powered by OpenAI GPT-4o mini",
    version="1.0.0",
    docs_url="/docs" if settings.ENVIRONMENT == "development" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT == "development" else None,
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {"status": "healthy", "service": "positivity-push-api"}

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "message": "Positivity Push API",
        "description": "WhatsApp-based AI coaching service",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "stripe_webhook": "/stripe/webhook", 
            "whatsapp_webhook": "/whatsapp/webhook",
            "docs": "/docs" if settings.ENVIRONMENT == "development" else "disabled"
        }
    }

# Include routers
app.include_router(stripe_webhook.router, prefix="/stripe", tags=["stripe"])
app.include_router(whatsapp_webhook.router, prefix="/whatsapp", tags=["whatsapp"])

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for production error management"""
    return JSONResponse(
        status_code=500,
        content={
            "message": "Internal server error",
            "detail": str(exc) if settings.ENVIRONMENT == "development" else "An error occurred"
        }
    )

if __name__ == "__main__":
    # Run with uvicorn for development
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=settings.ENVIRONMENT == "development",
        log_level="info"
    )