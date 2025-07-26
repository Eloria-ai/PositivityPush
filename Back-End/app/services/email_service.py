"""
Email Service for Positivity Push
Handles thank you emails, invoices, and notifications via SendGrid.
"""

import sendgrid
from sendgrid.helpers.mail import Mail, Email, To, Content
from typing import Dict, Any, Optional

from app.config import settings
from app.logging_config import get_logger

# Configure structured logging
logger = get_logger("app.services.email")

class EmailService:
    """Service class for email operations"""
    
    def __init__(self):
        self.sg = sendgrid.SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)
        self.from_email = Email(settings.FROM_EMAIL)
    
    async def send_welcome_email(
        self, 
        to_email: str, 
        subscription_data: Dict[str, Any]
    ) -> bool:
        """Send welcome/thank you email after payment"""
        try:
            to_email_obj = To(to_email)
            subject = "Welcome to Positivity Push! 🎉"
            
            html_content = self._build_welcome_email_html(subscription_data)
            content = Content("text/html", html_content)
            
            mail = Mail(self.from_email, to_email_obj, subject, content)
            
            response = self.sg.client.mail.send.post(request_body=mail.get())
            
            if response.status_code in [200, 202]:
                logger.info(f"Welcome email sent to {to_email}")
                return True
            else:
                logger.error(f"Failed to send welcome email: {response.body}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending welcome email: {e}")
            return False
    
    async def send_activation_reminder(
        self, 
        to_email: str, 
        whatsapp_activation_link: str
    ) -> bool:
        """Send reminder email if user hasn't activated WhatsApp"""
        try:
            to_email_obj = To(to_email)
            subject = "Don't forget to activate your AI coach! 🤖"
            
            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #10B981;">Almost there! 🎯</h2>
                
                <p>Hi there!</p>
                
                <p>We noticed you completed your payment for Positivity Push but haven't activated your AI coach yet.</p>
                
                <p>It only takes one click to start your personalized coaching journey:</p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{whatsapp_activation_link}" 
                       style="background-color: #10B981; color: white; padding: 15px 30px; 
                              text-decoration: none; border-radius: 8px; font-weight: bold;">
                        🚀 Activate Your AI Coach
                    </a>
                </div>
                
                <p>Your AI coach is waiting to help you with:</p>
                <ul>
                    <li>Daily personalized affirmations</li>
                    <li>Gratitude practice guidance</li>
                    <li>24/7 motivational support</li>
                    <li>Weekly progress reflections</li>
                </ul>
                
                <p>Ready to start your positivity journey?</p>
                
                <p>With encouragement,<br>
                The Positivity Push Team</p>
                
                <hr style="margin-top: 40px; border: none; border-top: 1px solid #eee;">
                <p style="font-size: 12px; color: #666;">
                    Questions? Reply to this email or contact us at support@positivitypush.com
                </p>
            </body>
            </html>
            """
            
            content = Content("text/html", html_content)
            mail = Mail(self.from_email, to_email_obj, subject, content)
            
            response = self.sg.client.mail.send.post(request_body=mail.get())
            
            if response.status_code in [200, 202]:
                logger.info(f"Activation reminder sent to {to_email}")
                return True
            else:
                logger.error(f"Failed to send activation reminder: {response.body}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending activation reminder: {e}")
            return False
    
    def _build_welcome_email_html(self, subscription_data: Dict[str, Any]) -> str:
        """Build welcome email HTML content"""
        plan_type = subscription_data.get('plan_type', '3_month')
        amount = subscription_data.get('amount_total', 0) / 100  # Convert from cents
        
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="text-align: center; padding: 20px; background-color: #10B981; color: white;">
                <h1>Welcome to Positivity Push! 🎉</h1>
            </div>
            
            <div style="padding: 30px 20px;">
                <h2>Thank you for your payment!</h2>
                
                <p>Hi there!</p>
                
                <p>Your payment of <strong>${amount:.2f}</strong> for the <strong>{plan_type.replace('_', '-')} plan</strong> has been successfully processed.</p>
                
                <div style="background-color: #F3F4F6; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="margin-top: 0; color: #10B981;">Next Step: Activate Your AI Coach 🤖</h3>
                    <p>Check your success page to get your WhatsApp activation link and start chatting with your personal AI coach!</p>
                </div>
                
                <h3>What you'll get:</h3>
                <ul>
                    <li>🌅 Personalized daily affirmations</li>
                    <li>🙏 Evening gratitude prompts</li>
                    <li>💬 24/7 conversational AI support</li>
                    <li>📊 Weekly progress reflections</li>
                    <li>🎯 Goal-setting and accountability</li>
                </ul>
                
                <p>Your AI coach learns your unique style and adapts to support your personal growth journey.</p>
                
                <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
                
                <h3>Questions or need help?</h3>
                <p>We're here to support you! Reach out anytime:</p>
                <ul>
                    <li>📧 Email: <a href="mailto:support@positivitypush.com">support@positivitypush.com</a></li>
                    <li>💬 WhatsApp: Once activated, just message your coach!</li>
                </ul>
                
                <p>Welcome to your positivity journey!</p>
                
                <p>With gratitude,<br>
                <strong>The Positivity Push Team</strong></p>
            </div>
            
            <div style="text-align: center; padding: 20px; background-color: #F9FAFB; font-size: 12px; color: #666;">
                <p>This email was sent because you completed a purchase at Positivity Push.</p>
                <p>Positivity Push • WhatsApp-based AI Coaching • positivity-push.vercel.app</p>
            </div>
        </body>
        </html>
        """

    async def send_payment_failed_email(
        self, 
        to_email: str, 
        customer_data: Dict[str, Any]
    ) -> bool:
        """Send payment failed notification email"""
        try:
            to_email_obj = To(to_email)
            subject = "Payment Issue - Positivity Push"
            
            html_content = self._build_payment_failed_email_html(customer_data)
            content = Content("text/html", html_content)
            
            mail = Mail(self.from_email, to_email_obj, subject, content)
            
            response = self.sg.client.mail.send.post(request_body=mail.get())
            
            if response.status_code in [200, 202]:
                logger.info(f"Payment failed email sent to {to_email}")
                return True
            else:
                logger.error(f"Failed to send payment failed email: {response.body}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending payment failed email: {e}")
            return False

    async def send_cancellation_email(
        self, 
        to_email: str, 
        customer_data: Dict[str, Any]
    ) -> bool:
        """Send subscription cancellation email"""
        try:
            to_email_obj = To(to_email)
            subject = "We're sorry to see you go - Positivity Push"
            
            html_content = self._build_cancellation_email_html(customer_data)
            content = Content("text/html", html_content)
            
            mail = Mail(self.from_email, to_email_obj, subject, content)
            
            response = self.sg.client.mail.send.post(request_body=mail.get())
            
            if response.status_code in [200, 202]:
                logger.info(f"Cancellation email sent to {to_email}")
                return True
            else:
                logger.error(f"Failed to send cancellation email: {response.body}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending cancellation email: {e}")
            return False

    def _build_payment_failed_email_html(self, customer_data: Dict[str, Any]) -> str:
        """Build payment failed email HTML content"""
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="text-align: center; padding: 20px; background-color: #EF4444; color: white;">
                <h1>Payment Issue - Action Required</h1>
            </div>
            
            <div style="padding: 30px 20px;">
                <h2>We couldn't process your payment</h2>
                
                <p>Hi there!</p>
                
                <p>We had trouble processing your recent payment for your Positivity Push subscription. This could be due to:</p>
                
                <ul>
                    <li>💳 Expired or invalid payment method</li>
                    <li>🏦 Insufficient funds</li>
                    <li>🔒 Bank security restrictions</li>
                    <li>📱 Outdated billing information</li>
                </ul>
                
                <div style="background-color: #FEF3C7; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #F59E0B;">
                    <h3 style="margin-top: 0; color: #92400E;">Your coaching is temporarily paused</h3>
                    <p>To continue receiving your daily affirmations and AI coaching, please update your payment method.</p>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="https://positivitypush.com/billing" style="background-color: #10B981; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                        Update Payment Method
                    </a>
                </div>
                
                <p>If you're having trouble or need help, please reach out to us:</p>
                <ul>
                    <li>📧 Email: <a href="mailto:support@positivitypush.com">support@positivitypush.com</a></li>
                    <li>💬 Reply to this email</li>
                </ul>
                
                <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
                
                <div style="text-align: center; color: #666; font-size: 14px;">
                    <p>© 2024 Positivity Push. We're here to support your journey.</p>
                </div>
            </div>
        </body>
        </html>
        """

    def _build_cancellation_email_html(self, customer_data: Dict[str, Any]) -> str:
        """Build cancellation email HTML content"""
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="text-align: center; padding: 20px; background-color: #6B7280; color: white;">
                <h1>We're sorry to see you go</h1>
            </div>
            
            <div style="padding: 30px 20px;">
                <h2>Your subscription has been cancelled</h2>
                
                <p>Hi there!</p>
                
                <p>We've successfully cancelled your Positivity Push subscription as requested. You'll continue to have access to your AI coach until the end of your current billing period.</p>
                
                <div style="background-color: #F3F4F6; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="margin-top: 0; color: #374151;">What happens next:</h3>
                    <ul>
                        <li>✅ No future charges will be made</li>
                        <li>📱 Your AI coach remains active until your plan expires</li>
                        <li>💾 Your progress and preferences are safely stored</li>
                        <li>🔄 You can reactivate anytime</li>
                    </ul>
                </div>
                
                <h3>We'd love your feedback</h3>
                <p>Your experience helps us improve. Would you mind sharing why you decided to leave?</p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="https://positivitypush.com/feedback" style="background-color: #6B7280; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                        Share Feedback
                    </a>
                </div>
                
                <div style="background-color: #ECFDF5; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #10B981;">
                    <h3 style="margin-top: 0; color: #065F46;">Ready to come back?</h3>
                    <p>We'll be here when you're ready to continue your positivity journey. Your AI coach is always excited to support you!</p>
                    <p style="text-align: center; margin-top: 15px;">
                        <a href="https://positivitypush.com" style="color: #10B981; text-decoration: none; font-weight: bold;">Reactivate Your Subscription</a>
                    </p>
                </div>
                
                <p>Thank you for being part of our community. We wish you all the best on your journey!</p>
                
                <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
                
                <div style="text-align: center; color: #666; font-size: 14px;">
                    <p>© 2024 Positivity Push. Keep spreading positivity! 🌟</p>
                </div>
            </div>
        </body>
        </html>
        """
