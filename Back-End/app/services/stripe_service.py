"""
Stripe Service for Positivity Push
Handles Stripe payment processing and subscription management.
"""

from typing import Dict, Any, Optional
import stripe
import logging

logger = logging.getLogger(__name__)

class StripeService:
    """Service class for Stripe operations"""
    
    def __init__(self, stripe_client):
        self.stripe = stripe_client
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve Stripe checkout session"""
        try:
            session = self.stripe.checkout.Session.retrieve(session_id)
            return session
        except stripe.error.StripeError as e:
            logger.error(f"Error retrieving Stripe session: {e}")
            return None
    
    async def get_customer(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve Stripe customer"""
        try:
            customer = self.stripe.Customer.retrieve(customer_id)
            return customer
        except stripe.error.StripeError as e:
            logger.error(f"Error retrieving Stripe customer: {e}")
            return None
    
    async def get_subscription(self, subscription_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve Stripe subscription"""
        try:
            subscription = self.stripe.Subscription.retrieve(subscription_id)
            return subscription
        except stripe.error.StripeError as e:
            logger.error(f"Error retrieving Stripe subscription: {e}")
            return None
    
    async def cancel_subscription(self, subscription_id: str) -> bool:
        """Cancel Stripe subscription"""
        try:
            self.stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=True
            )
            logger.info(f"Cancelled subscription: {subscription_id}")
            return True
        except stripe.error.StripeError as e:
            logger.error(f"Error cancelling subscription: {e}")
            return False
    
    async def create_billing_portal_session(self, customer_id: str, return_url: str) -> Optional[str]:
        """Create Stripe billing portal session for customer self-service"""
        try:
            session = self.stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=return_url
            )
            return session.url
        except stripe.error.StripeError as e:
            logger.error(f"Error creating billing portal session: {e}")
            return None