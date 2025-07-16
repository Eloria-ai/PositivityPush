"""
Timezone Detection Service
Automatically detects user timezone from IP address and other methods
"""

import logging
import requests
from typing import Optional
from datetime import datetime
import pytz

logger = logging.getLogger(__name__)

class TimezoneDetector:
    """Detects user timezone automatically"""
    
    def __init__(self):
        self.default_timezone = "UTC"
    
    def detect_timezone_from_ip(self, ip_address: str) -> Optional[str]:
        """
        Detect timezone from IP address using ipapi.co
        """
        try:
            # Skip local/private IPs
            if self._is_local_ip(ip_address):
                return self.default_timezone
            
            # Call IP geolocation API
            response = requests.get(
                f"https://ipapi.co/{ip_address}/timezone/",
                timeout=5
            )
            
            if response.status_code == 200:
                timezone_name = response.text.strip()
                
                # Validate timezone
                if self._is_valid_timezone(timezone_name):
                    # Convert to our standard timezone codes
                    return self._convert_timezone_to_standard(timezone_name)
                
        except Exception as e:
            logger.error(f"Error detecting timezone from IP {ip_address}: {e}")
        
        return self.default_timezone
    
    def detect_timezone_from_whatsapp_metadata(self, whatsapp_data: dict) -> Optional[str]:
        """
        Detect timezone from WhatsApp metadata if available
        """
        try:
            # WhatsApp Business API may provide location data
            if "location" in whatsapp_data:
                # This would require WhatsApp location permissions
                pass
            
            # Check for any timezone hints in metadata
            if "timezone" in whatsapp_data:
                return whatsapp_data["timezone"]
                
        except Exception as e:
            logger.error(f"Error detecting timezone from WhatsApp metadata: {e}")
        
        return None
    
    def get_timezone_from_current_time_hint(self, user_message: str) -> Optional[str]:
        """
        Try to detect timezone from time-related hints in user messages
        """
        try:
            # Look for time references that might indicate timezone
            current_hour = datetime.now().hour
            
            # Basic heuristic: if user mentions it's morning/evening
            # and it doesn't match UTC, try to infer timezone
            if "morning" in user_message.lower() and current_hour > 12:
                # User says morning but it's afternoon in UTC
                # They might be in a western timezone
                return "PST"  # This is very basic, needs improvement
            
        except Exception as e:
            logger.error(f"Error detecting timezone from time hint: {e}")
        
        return None
    
    def _is_local_ip(self, ip: str) -> bool:
        """Check if IP is local/private"""
        local_prefixes = [
            "127.", "192.168.", "10.", "172.16.", "172.17.", "172.18.",
            "172.19.", "172.20.", "172.21.", "172.22.", "172.23.", "172.24.",
            "172.25.", "172.26.", "172.27.", "172.28.", "172.29.", "172.30.",
            "172.31.", "::1", "localhost"
        ]
        
        for prefix in local_prefixes:
            if ip.startswith(prefix):
                return True
        
        return False
    
    def _is_valid_timezone(self, timezone_name: str) -> bool:
        """Validate timezone name"""
        try:
            pytz.timezone(timezone_name)
            return True
        except pytz.UnknownTimeZoneError:
            return False
    
    def _convert_timezone_to_standard(self, timezone_name: str) -> str:
        """Convert timezone name to our standard format"""
        # Map common timezone names to our standard codes
        timezone_mapping = {
            "America/New_York": "EST",
            "America/Chicago": "CST", 
            "America/Denver": "MST",
            "America/Los_Angeles": "PST",
            "Europe/London": "GMT",
            "Europe/Paris": "CET",
            "Europe/Berlin": "CET",
            "Asia/Tokyo": "JST",
            "Australia/Sydney": "AEST",
            "UTC": "UTC"
        }
        
        # Direct mapping
        if timezone_name in timezone_mapping:
            return timezone_mapping[timezone_name]
        
        # Try to extract from timezone name
        if "New_York" in timezone_name or "Eastern" in timezone_name:
            return "EST"
        elif "Chicago" in timezone_name or "Central" in timezone_name:
            return "CST"
        elif "Denver" in timezone_name or "Mountain" in timezone_name:
            return "MST"
        elif "Los_Angeles" in timezone_name or "Pacific" in timezone_name:
            return "PST"
        elif "London" in timezone_name or "GMT" in timezone_name:
            return "GMT"
        elif "Paris" in timezone_name or "Berlin" in timezone_name or "CET" in timezone_name:
            return "CET"
        elif "Tokyo" in timezone_name or "JST" in timezone_name:
            return "JST"
        elif "Sydney" in timezone_name or "Melbourne" in timezone_name:
            return "AEST"
        
        # Default to UTC if no mapping found
        return "UTC"