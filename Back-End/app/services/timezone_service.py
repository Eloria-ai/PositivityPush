"""
Timezone Service for Positivity Push
Handles manual timezone extraction from user input - privacy-first approach
"""

import logging
import re
from typing import Optional
from zoneinfo import available_timezones

logger = logging.getLogger(__name__)

# Regex pattern for extracting IANA timezone from natural language
IANA_RE = re.compile(r"\b([A-Za-z]+/[A-Za-z_\-]+)\b")

class TimezoneService:
    """Service for extracting timezones from user input - privacy-first approach"""
    
    def extract_timezone(self, text: str) -> Optional[str]:
        """
        Extract IANA timezone from natural language text.
        Supports both "Region/City" format and city-only inputs.
        
        Args:
            text: User input like "I'm in London now", "Amsterdam", or "Africa/Casablanca"
            
        Returns:
            Valid IANA timezone string or None if none found
        """
        # First try to find Region/City format
        m = IANA_RE.search(text)
        if m and m.group(1) in available_timezones():
            return m.group(1)
        
        # If not found, try city-only mappings
        return self._map_city_to_timezone(text)
    
    def _map_city_to_timezone(self, text: str) -> Optional[str]:
        """
        Accept inputs like "Amsterdam" or "new york" and
        return a matching Region/City IANA timezone string.

        Strategy:
        1. Normalise the city name (lower-case, strip punctuation/whitespace).
        2. Scan all available IANA zones; if the trailing part of the zone
           matches the city token (case-insensitive, '_' and '-' treated as spaces),
           return that zone.
        3. Fallback to a small manual map for ambiguous cases (e.g. "new york" → "America/New_York").
        """
        city_token = re.sub(r'[^a-z]', '', text.lower())

        # fast manual overrides for common cities
        manual = {
            "amsterdam": "Europe/Amsterdam",
            "london": "Europe/London",
            "paris": "Europe/Paris",
            "berlin": "Europe/Berlin",
            "madrid": "Europe/Madrid",
            "rome": "Europe/Rome",
            "cairo": "Africa/Cairo",
            "nairobi": "Africa/Nairobi",
            "newyork": "America/New_York",
            "losangeles": "America/Los_Angeles",
            "chicago": "America/Chicago",
            "denver": "America/Denver",
            "sydney": "Australia/Sydney",
            "melbourne": "Australia/Melbourne",
            "tokyo": "Asia/Tokyo",
            "shanghai": "Asia/Shanghai",
            "singapore": "Asia/Singapore",
            "dubai": "Asia/Dubai",
            "mumbai": "Asia/Kolkata",
            "delhi": "Asia/Kolkata",
        }
        if city_token in manual:
            return manual[city_token]

        # brute-force search through IANA list
        for zone in available_timezones():
            city_part = zone.split('/')[-1].lower().replace('_', '').replace('-', '')
            if city_part == city_token:
                return zone

        return None