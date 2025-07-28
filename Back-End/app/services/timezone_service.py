"""
AI-Powered Timezone Service for Positivity Push
Uses OpenAI to intelligently extract timezones from any location worldwide
"""

import re
import json
from typing import Optional
from zoneinfo import available_timezones
import openai

from app.config import settings
from app.logging_config import get_logger

# Configure structured logging
logger = get_logger("app.services.timezone")

# Regex pattern for extracting IANA timezone from natural language
IANA_RE = re.compile(r"\b([A-Za-z]+/[A-Za-z_\-]+)\b")

class TimezoneService:
    """AI-powered service for extracting timezones from user input globally"""
    
    def __init__(self):
        self.openai_client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
    
    def extract_timezone(self, text: str) -> Optional[str]:
        """
        Extract IANA timezone from natural language text using AI.
        Handles any city, country, or location worldwide.
        
        Args:
            text: User input like "I'm in Buenos Aires", "Tokyo", "small town in Germany", etc.
            
        Returns:
            Valid IANA timezone string or None if none found
        """
        if not text:
            return None
            
        # First try to find explicit Region/City format
        m = IANA_RE.search(text)
        if m and m.group(1) in available_timezones():
            logger.info(f"Found explicit IANA timezone: {m.group(1)}")
            return m.group(1)
        
        # Use AI to intelligently extract timezone from any location
        return self._ai_extract_timezone(text)
    
    def _ai_extract_timezone(self, text: str) -> Optional[str]:
        """
        Use OpenAI to intelligently extract timezone from any location worldwide.
        This can handle cities, countries, regions, or even descriptions like "small town in Germany"
        """
        try:
            prompt = f"""
Extract the IANA timezone from this user message: "{text}"

Rules:
1. Return ONLY a valid IANA timezone string (e.g., "Europe/London", "Asia/Tokyo")
2. If multiple locations are mentioned, use the first/primary one
3. If you can't determine a specific location, return "UNKNOWN"
4. For ambiguous cities, choose the most populous/well-known one
5. Handle variations like "NYC" → "America/New_York", "LA" → "America/Los_Angeles"

Examples:
- "I'm in London now" → "Europe/London"
- "Tokyo" → "Asia/Tokyo" 
- "small town in Germany" → "Europe/Berlin"
- "NYC" → "America/New_York"
- "I moved to Buenos Aires" → "America/Argentina/Buenos_Aires"
- "random text with no location" → "UNKNOWN"

Response format: Just the timezone string, nothing else.
"""

            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a timezone extraction expert. Return only valid IANA timezone strings."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=50,
                temperature=0.1
            )
            
            ai_timezone = response.choices[0].message.content.strip()
            
            # Validate the AI response
            if ai_timezone == "UNKNOWN" or not ai_timezone:
                logger.info(f"AI could not determine timezone from: {text}")
                return None
            
            # Verify it's a valid IANA timezone
            if ai_timezone in available_timezones():
                logger.info(f"AI extracted timezone: '{text}' → {ai_timezone}")
                return ai_timezone
            else:
                logger.warning(f"AI returned invalid timezone: {ai_timezone}")
                return None
                
        except Exception as e:
            logger.error(f"Error in AI timezone extraction: {e}")
            # Fallback to basic city search if AI fails
            return self._fallback_city_search(text)
    
    def _fallback_city_search(self, text: str) -> Optional[str]:
        """
        Fallback method for basic city matching if AI fails
        Only covers major world cities as a safety net
        """
        # Basic fallback for major cities only
        basic_cities = {
            "london": "Europe/London", "paris": "Europe/Paris", "berlin": "Europe/Berlin",
            "tokyo": "Asia/Tokyo", "sydney": "Australia/Sydney", "new york": "America/New_York",
            "los angeles": "America/Los_Angeles", "chicago": "America/Chicago",
            "dubai": "Asia/Dubai", "singapore": "Asia/Singapore", "mumbai": "Asia/Kolkata"
        }
        
        text_lower = text.lower()
        for city, timezone in basic_cities.items():
            if city in text_lower:
                logger.info(f"Fallback matched: {city} → {timezone}")
                return timezone
                
        return None
