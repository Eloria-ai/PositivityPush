"""
WhatsApp Service for Positivity Push
Handles Twilio WhatsApp API communication for sending messages.
"""

import httpx
import json
from typing import Dict, Any, Optional
import base64

from app.config import settings
from app.logging_config import get_logger

# Configure structured logging
logger = get_logger("app.services.whatsapp")

class WhatsAppService:
    """Service class for Twilio WhatsApp API operations"""
    
    def __init__(self):
        self.base_url = f"https://api.twilio.com/2010-04-01/Accounts/{settings.TWILIO_ACCOUNT_SID}"
        # Twilio uses Basic Auth with Account SID and Auth Token
        credentials = f"{settings.TWILIO_ACCOUNT_SID}:{settings.TWILIO_AUTH_TOKEN}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        self.headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
    
    async def send_message(self, to: str, message: str) -> bool:
        """Send text message via Twilio WhatsApp"""
        try:
            async with httpx.AsyncClient() as client:
                # Twilio WhatsApp format: whatsapp:+1234567890
                formatted_to = f"whatsapp:{to}" if not to.startswith("whatsapp:") else to
                formatted_from = f"whatsapp:{settings.TWILIO_WHATSAPP_NUMBER}"
                
                # Twilio uses form data
                payload = {
                    "From": formatted_from,
                    "To": formatted_to,
                    "Body": message
                }
                
                response = await client.post(
                    f"{self.base_url}/Messages.json",
                    headers=self.headers,
                    data=payload  # Form data, not JSON
                )
                
                if response.status_code in [200, 201]:
                    logger.info("whatsapp_message_sent",
                               recipient=to,
                               status_code=response.status_code)
                    return True
                else:
                    logger.error("whatsapp_message_failed",
                               recipient=to,
                               status_code=response.status_code,
                               error_text=response.text)
                    return False
                    
        except Exception as e:
            logger.error("whatsapp_message_exception",
                        recipient=to,
                        error=str(e),
                        exc_info=True)
            return False
    
    async def send_template_message(
        self, 
        to: str, 
        template_name: str, 
        parameters: list = None
    ) -> bool:
        """Send template message via WhatsApp"""
        try:
            async with httpx.AsyncClient() as client:
                payload = {
                    "messaging_product": "whatsapp",
                    "to": to,
                    "type": "template",
                    "template": {
                        "name": template_name,
                        "language": {"code": "en_US"}
                    }
                }
                
                if parameters:
                    payload["template"]["components"] = [
                        {
                            "type": "body",
                            "parameters": parameters
                        }
                    ]
                
                response = await client.post(
                    f"{self.base_url}/messages",
                    headers=self.headers,
                    json=payload
                )
                
                if response.status_code == 200:
                    logger.info("whatsapp_template_sent",
                               recipient=to,
                               template_name=template_name)
                    return True
                else:
                    logger.error("whatsapp_template_failed",
                               recipient=to,
                               template_name=template_name,
                               error_text=response.text)
                    return False
                    
        except Exception as e:
            logger.error("whatsapp_template_exception",
                        recipient=to,
                        template_name=template_name,
                        error=str(e),
                        exc_info=True)
            return False
    
    async def mark_message_as_read(self, message_id: str) -> bool:
        """Mark incoming message as read"""
        try:
            async with httpx.AsyncClient() as client:
                payload = {
                    "messaging_product": "whatsapp",
                    "status": "read",
                    "message_id": message_id
                }
                
                response = await client.post(
                    f"{self.base_url}/messages",
                    headers=self.headers,
                    json=payload
                )
                
                return response.status_code == 200
                    
        except Exception as e:
            logger.error("whatsapp_read_mark_exception",
                        message_id=message_id,
                        error=str(e),
                        exc_info=True)
            return False
    
    async def send_reaction(self, message_id: str, emoji: str, to: str) -> bool:
        """Send reaction to a message"""
        try:
            async with httpx.AsyncClient() as client:
                payload = {
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": to,
                    "type": "reaction",
                    "reaction": {
                        "message_id": message_id,
                        "emoji": emoji
                    }
                }
                
                response = await client.post(
                    f"{self.base_url}/messages",
                    headers=self.headers,
                    json=payload
                )
                
                return response.status_code == 200
                    
        except Exception as e:
            logger.error("whatsapp_reaction_exception",
                        message_id=message_id,
                        recipient=to,
                        emoji=emoji,
                        error=str(e),
                        exc_info=True)
            return False
