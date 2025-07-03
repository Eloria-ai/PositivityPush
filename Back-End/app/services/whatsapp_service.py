"""
WhatsApp Service for Positivity Push
Handles WhatsApp Cloud API communication for sending messages.
"""

import httpx
import json
import logging
from typing import Dict, Any, Optional

from app.config import settings

logger = logging.getLogger(__name__)

class WhatsAppService:
    """Service class for WhatsApp Cloud API operations"""
    
    def __init__(self):
        self.base_url = f"https://graph.facebook.com/v18.0/{settings.WA_PHONE_ID}"
        self.headers = {
            "Authorization": f"Bearer {settings.WA_TOKEN}",
            "Content-Type": "application/json"
        }
    
    async def send_message(self, to: str, message: str) -> bool:
        """Send text message via WhatsApp"""
        try:
            async with httpx.AsyncClient() as client:
                payload = {
                    "messaging_product": "whatsapp",
                    "to": to,
                    "type": "text",
                    "text": {"body": message}
                }
                
                response = await client.post(
                    f"{self.base_url}/messages",
                    headers=self.headers,
                    json=payload
                )
                
                if response.status_code == 200:
                    logger.info(f"Message sent successfully to {to}")
                    return True
                else:
                    logger.error(f"Failed to send message: {response.text}")
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