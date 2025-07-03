"""
Email Service for Positivity Push
Handles thank you emails, invoices, and notifications via SendGrid.
"""

import sendgrid
from sendgrid.helpers.mail import Mail, Email, To, Content
import logging
from typing import Dict, Any, Optional

from app.config import settings

logger = logging.getLogger(__name__)

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