"""
Stripe Webhook Handler for Positivity Push
Handles payment events and subscription management.
"""

from fastapi import APIRouter, Request, HTTPException, Depends, status
from fastapi.responses import JSONResponse
import stripe
import json
import logging
from typing import Dict, Any

from app.config import settings
from app.deps import get_supabase_client, get_stripe_client
from app.services.stripe_service import StripeService
from app.services.supabase_client import SupabaseService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    db = Depends(get_supabase_client),
    stripe_client = Depends(get_stripe_client)
):
    """
    Handle Stripe webhook events
    Critical events: checkout.session.completed, invoice.payment_succeeded, etc.
    """
    
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')
    
    if not sig_header:
        logger.error("Missing Stripe signature header")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing Stripe signature"
        )
    
    try:
        # Verify webhook signature
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
        logger.info(f"Received Stripe event: {event['type']}")
        
    except ValueError as e:
        logger.error(f"Invalid payload: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid payload"
        )
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Invalid signature: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid signature"
        )
    
    # Initialize services
    stripe_service = StripeService(stripe_client)
    supabase_service = SupabaseService(db)
    
    try:
        # Handle different event types
        if event['type'] == 'checkout.session.completed':
            await handle_checkout_completed(event['data']['object'], supabase_service)
            
        elif event['type'] == 'invoice.payment_succeeded':
            await handle_payment_succeeded(event['data']['object'], supabase_service)
            
        elif event['type'] == 'invoice.payment_failed':
            await handle_payment_failed(event['data']['object'], supabase_service)
            
        elif event['type'] == 'customer.subscription.updated':
            await handle_subscription_updated(event['data']['object'], supabase_service)
            
        elif event['type'] == 'customer.subscription.deleted':
            await handle_subscription_cancelled(event['data']['object'], supabase_service)
            
        else:
            logger.info(f"Unhandled event type: {event['type']}")
    
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook processing failed"
        )
    
    return JSONResponse(content={"status": "success"})

async def handle_checkout_completed(session: Dict[str, Any], supabase_service: SupabaseService):
    """
    Handle successful checkout completion
    Creates subscription record in database
    """
    logger.info(f"Processing checkout completion for session: {session['id']}")
    
    # Extract customer information
    customer_email = session.get('customer_details', {}).get('email')
    phone_number = session.get('custom_fields', [{}])[0].get('text', {}).get('value') if session.get('custom_fields') else None
    
    # Create subscription record
    subscription_data = {
        "stripe_session_id": session['id'],
        "stripe_customer_id": session.get('customer'),
        "email": customer_email,
        "phone_number": phone_number,
        "amount_total": session['amount_total'],
        "currency": session['currency'],
        "status": "paid_pending_optin",
        "plan_type": determine_plan_type(session['amount_total']),
        "created_at": "now()",
    }
    
    await supabase_service.create_subscription(subscription_data)
    
    # TODO: Send thank you email
    logger.info(f"Subscription created for session: {session['id']}")

async def handle_payment_succeeded(invoice: Dict[str, Any], supabase_service: SupabaseService):
    """Handle successful recurring payment"""
    logger.info(f"Processing payment success for invoice: {invoice['id']}")
    
    # Update subscription status if needed
    customer_id = invoice['customer']
    await supabase_service.update_subscription_by_customer(
        customer_id, 
        {"status": "active", "last_payment_at": "now()"}
    )

async def handle_payment_failed(invoice: Dict[str, Any], supabase_service: SupabaseService):
    """Handle failed recurring payment"""
    logger.info(f"Processing payment failure for invoice: {invoice['id']}")
    
    customer_id = invoice['customer']
    await supabase_service.update_subscription_by_customer(
        customer_id,
        {"status": "payment_failed", "failed_payment_at": "now()"}
    )

async def handle_subscription_updated(subscription: Dict[str, Any], supabase_service: SupabaseService):
    """Handle subscription updates"""
    logger.info(f"Processing subscription update: {subscription['id']}")
    
    # Update subscription details in database
    await supabase_service.update_subscription_by_stripe_id(
        subscription['id'],
        {
            "status": subscription['status'],
            "current_period_end": subscription['current_period_end'],
            "updated_at": "now()"
        }
    )

async def handle_subscription_cancelled(subscription: Dict[str, Any], supabase_service: SupabaseService):
    """Handle subscription cancellation"""
    logger.info(f"Processing subscription cancellation: {subscription['id']}")
    
    await supabase_service.update_subscription_by_stripe_id(
        subscription['id'],
        {
            "status": "cancelled",
            "cancelled_at": "now()"
        }
    )

def determine_plan_type(amount_total: int) -> str:
    """Determine plan type based on payment amount"""
    # Amount is in cents
    if amount_total >= 15000:  # $150+ = 6 month
        return "6_month"
    else:  # $75+ = 3 month
        return "3_month"

@router.get("/health")
async def stripe_health():
    """Health check for Stripe integration"""
    return {"status": "healthy", "service": "stripe-webhook"}