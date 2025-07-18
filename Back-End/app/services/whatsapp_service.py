"""
WhatsApp Service for Positivity Push
Handles Twilio WhatsApp API communication for sending messages.
"""

import httpx
import json
import logging
from typing import Dict, Any, Optional
import base64

from app.config import settings

logger = logging.getLogger(__name__)

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
                    logger.info(f"Message sent successfully to {to}")
                    return True
                else:
                    logger.error(f"Failed to send message: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error sending WhatsApp message: {e}")
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
                    logger.info(f"Template message sent successfully to {to}")
                    return True
                else:
                    logger.error(f"Failed to send template message: {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error sending WhatsApp template message: {e}")
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
            logger.error(f"Error marking message as read: {e}")
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
            logger.error(f"Error sending reaction: {e}")
            return False
