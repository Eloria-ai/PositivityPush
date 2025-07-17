"""
Timezone Detection Service for Positivity Push
Handles phone-based and IP-based timezone detection and updates for traveling users
"""

import logging
import httpx
import re
from typing import Optional, Dict, Any
from datetime import datetime, timezone
import pytz

logger = logging.getLogger(__name__)

class TimezoneService:
    """Service for detecting and managing user timezones from phone and IP"""
    
    def __init__(self):
        self.ip_api_url = "http://ip-api.com/json/"
        self.backup_api_url = "https://ipapi.co/"
        
    async def detect_timezone_from_ip(self, ip_address: str) -> Optional[str]:
        """
        Detect timezone from IP address using external APIs
        
        Args:
            ip_address: The user's IP address
            
        Returns:
            Timezone string (e.g. "America/New_York") or None if detection fails
        """
        if not ip_address or ip_address in ["127.0.0.1", "localhost", "::1"]:
            logger.warning(f"Invalid IP address for timezone detection: {ip_address}")
            return "UTC"  # Default to UTC for local/invalid IPs
        
        try:
            # Try primary API (ip-api.com)
            timezone = await self._try_ip_api(ip_address)
            if timezone:
                return timezone
                
            # Try backup API (ipapi.co)
            timezone = await self._try_ipapi_co(ip_address)
            if timezone:
                return timezone
                
            logger.warning(f"Could not detect timezone for IP {ip_address}")
            return "UTC"  # Default fallback
            
        except Exception as e:
            logger.error(f"Error detecting timezone for IP {ip_address}: {e}")
            return "UTC"
    
    async def _try_ip_api(self, ip_address: str) -> Optional[str]:
        """Try timezone detection using ip-api.com"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.ip_api_url}{ip_address}")
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == "success":
                        timezone = data.get("timezone")
                        if timezone and self._validate_timezone(timezone):
                            logger.info(f"Detected timezone {timezone} for IP {ip_address} via ip-api.com")
                            return timezone
                        
        except Exception as e:
            logger.error(f"Error with ip-api.com for IP {ip_address}: {e}")
        
        return None
    
    async def _try_ipapi_co(self, ip_address: str) -> Optional[str]:
        """Try timezone detection using ipapi.co"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.backup_api_url}{ip_address}/timezone/")
                
                if response.status_code == 200:
                    timezone = response.text.strip()
                    if timezone and self._validate_timezone(timezone):
                        logger.info(f"Detected timezone {timezone} for IP {ip_address} via ipapi.co")
                        return timezone
                        
        except Exception as e:
            logger.error(f"Error with ipapi.co for IP {ip_address}: {e}")
        
        return None
    
    def _validate_timezone(self, timezone: str) -> bool:
        """Validate that the timezone string is a valid pytz timezone"""
        try:
            pytz.timezone(timezone)
            return True
        except pytz.exceptions.UnknownTimeZoneError:
            logger.warning(f"Invalid timezone: {timezone}")
            return False
    
    def get_current_time_in_timezone(self, timezone_str: str) -> datetime:
        """Get current time in the specified timezone"""
        try:
            tz = pytz.timezone(timezone_str)
            return datetime.now(tz)
        except pytz.exceptions.UnknownTimeZoneError:
            logger.warning(f"Unknown timezone {timezone_str}, using UTC")
            return datetime.now(pytz.UTC)
    
    def convert_user_time_to_utc(self, user_time: str, user_timezone: str) -> Optional[datetime]:
        """
        Convert user's local time to UTC for storage
        
        Args:
            user_time: Time in format "HH:MM"
            user_timezone: User's timezone string
            
        Returns:
            UTC datetime object or None if conversion fails
        """
        try:
            # Parse the time
            hour, minute = map(int, user_time.split(':'))
            
            # Create timezone object
            tz = pytz.timezone(user_timezone)
            
            # Get current date in user's timezone
            now = datetime.now(tz)
            
            # Create time for today in user's timezone
            local_time = tz.localize(datetime(now.year, now.month, now.day, hour, minute))
            
            # Convert to UTC
            utc_time = local_time.astimezone(pytz.UTC)
            
            return utc_time
            
        except Exception as e:
            logger.error(f"Error converting time {user_time} in timezone {user_timezone}: {e}")
            return None
    
    def format_time_for_user(self, utc_time: datetime, user_timezone: str) -> str:
        """
        Format UTC time for display in user's timezone
        
        Args:
            utc_time: UTC datetime object
            user_timezone: User's timezone string
            
        Returns:
            Formatted time string in 12-hour format
        """
        try:
            # Convert UTC to user's timezone
            tz = pytz.timezone(user_timezone)
            local_time = utc_time.astimezone(tz)
            
            # Format in 12-hour format
            return local_time.strftime("%I:%M %p")
            
        except Exception as e:
            logger.error(f"Error formatting time for timezone {user_timezone}: {e}")
            return utc_time.strftime("%I:%M %p UTC")
    
    def get_timezone_offset(self, timezone_str: str) -> str:
        """Get timezone offset string (e.g., '+05:30', '-08:00')"""
        try:
            tz = pytz.timezone(timezone_str)
            now = datetime.now(tz)
            offset = now.strftime('%z')
            
            # Format as +HH:MM or -HH:MM
            if len(offset) == 5:
                return f"{offset[:3]}:{offset[3:]}"
            return offset
            
        except Exception as e:
            logger.error(f"Error getting offset for timezone {timezone_str}: {e}")
            return "+00:00"
    
    
    # Phone-based timezone detection methods
    def detect_timezone_from_phone(self, message: Dict[str, Any]) -> Optional[str]:
        """
        Detect timezone from WhatsApp message metadata (phone-based)
        This is the preferred method as it's more accurate than IP detection
        
        LIMITATIONS:
        - WhatsApp typically provides Unix timestamps without timezone offsets
        - Phone metadata rarely includes explicit timezone information
        - Success rate depends on WhatsApp API version and message format
        - May often return None, requiring IP-based fallback
        
        Args:
            message: WhatsApp message object with timestamp and metadata
            
        Returns:
            Timezone string (e.g. "America/New_York") or None if detection fails
        """
        try:
            # Method 1: Check if timestamp includes timezone information
            timestamp = message.get("timestamp")
            if timestamp:
                timezone_str = self._extract_timezone_from_timestamp(timestamp)
                if timezone_str:
                    logger.info(f"Detected timezone {timezone_str} from message timestamp")
                    return timezone_str
            
            # Method 2: Check message metadata for timezone hints
            metadata = message.get("metadata", {})
            if metadata:
                timezone_str = self._extract_timezone_from_metadata(metadata)
                if timezone_str:
                    logger.info(f"Detected timezone {timezone_str} from message metadata")
                    return timezone_str
            
            # Method 3: Check for timezone in message headers or context
            context = message.get("context", {})
            if context:
                timezone_str = self._extract_timezone_from_context(context)
                if timezone_str:
                    logger.info(f"Detected timezone {timezone_str} from message context")
                    return timezone_str
            
            # Method 4: Try to extract from phone settings fields
            timezone_str = self._get_timezone_from_phone_settings(message)
            if timezone_str:
                logger.info(f"Detected timezone {timezone_str} from phone settings")
                return timezone_str
                    
            logger.warning("Could not detect timezone from phone message metadata")
            return None
            
        except Exception as e:
            logger.error(f"Error detecting timezone from phone metadata: {e}")
            return None
    
    def _extract_timezone_from_timestamp(self, timestamp: Any) -> Optional[str]:
        """Extract timezone from message timestamp"""
        try:
            # Handle Unix timestamp with timezone offset
            if isinstance(timestamp, (int, float)):
                # Convert to datetime to check if it has timezone info
                # For now, we can't determine timezone from UTC timestamp alone
                return None
            
            # Handle ISO 8601 timestamp with timezone
            if isinstance(timestamp, str):
                # Look for timezone indicators in ISO format
                # Examples: "2024-01-01T12:00:00-05:00", "2024-01-01T12:00:00+02:00"
                timezone_match = re.search(r'([+-]\d{2}):?(\d{2})$', timestamp)
                if timezone_match:
                    offset_str = f"{timezone_match.group(1)}:{timezone_match.group(2)}"
                    return self._offset_to_timezone(offset_str)
                
                # Look for timezone abbreviations
                tz_match = re.search(r'\b([A-Z]{3,4})\b$', timestamp)
                if tz_match:
                    return self._abbreviation_to_timezone(tz_match.group(1))
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting timezone from timestamp: {e}")
            return None
    
    def _extract_timezone_from_metadata(self, metadata: Dict[str, Any]) -> Optional[str]:
        """Extract timezone from message metadata"""
        try:
            # Check for explicit timezone field
            timezone_field = metadata.get("timezone")
            if timezone_field:
                if self._validate_timezone(timezone_field):
                    return timezone_field
            
            # Check for locale information
            locale = metadata.get("locale")
            if locale:
                timezone_str = self._locale_to_timezone(locale)
                if timezone_str:
                    return timezone_str
            
            # Check for device timezone
            device_timezone = metadata.get("device_timezone")
            if device_timezone:
                if self._validate_timezone(device_timezone):
                    return device_timezone
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting timezone from metadata: {e}")
            return None
    
    def _extract_timezone_from_context(self, context: Dict[str, Any]) -> Optional[str]:
        """Extract timezone from message context"""
        try:
            # Check for user agent or device info
            user_agent = context.get("user_agent")
            if user_agent:
                # Parse user agent for timezone hints
                timezone_str = self._parse_user_agent_timezone(user_agent)
                if timezone_str:
                    return timezone_str
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting timezone from context: {e}")
            return None
    
    def _get_timezone_from_phone_settings(self, message: Dict[str, Any]) -> Optional[str]:
        """
        Attempt to extract timezone from phone system settings
        This would work if WhatsApp includes device timezone in message metadata
        """
        try:
            # Check various fields where timezone might be embedded
            fields_to_check = [
                "device_timezone",
                "system_timezone", 
                "local_timezone",
                "tz",
                "timezone",
                "time_zone"
            ]
            
            for field in fields_to_check:
                value = message.get(field)
                if value and self._validate_timezone(value):
                    logger.info(f"Found timezone {value} in field {field}")
                    return value
            
            # Check nested metadata
            metadata = message.get("metadata", {})
            for field in fields_to_check:
                value = metadata.get(field)
                if value and self._validate_timezone(value):
                    logger.info(f"Found timezone {value} in metadata.{field}")
                    return value
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting timezone from phone settings: {e}")
            return None
    
    def _offset_to_timezone(self, offset_str: str) -> Optional[str]:
        """Convert timezone offset to timezone name"""
        try:
            # Common offset mappings - handle seasonal changes with priority
            offset_mappings = {
                # US Eastern Time
                "-05:00": "America/New_York",  # EST (winter)
                "-04:00": "America/New_York",  # EDT (summer)
                
                # US Central Time  
                "-06:00": "America/Chicago",   # CST (winter)
                "-05:00": "America/Chicago",   # CDT (summer) - NOTE: conflicts with EST, EST takes priority
                
                # US Mountain Time
                "-07:00": "America/Denver",    # MST (winter)
                "-06:00": "America/Denver",    # MDT (summer) - NOTE: conflicts with CST, CST takes priority
                
                # US Pacific Time
                "-08:00": "America/Los_Angeles", # PST (winter)
                "-07:00": "America/Los_Angeles", # PDT (summer) - NOTE: conflicts with MST, MST takes priority
                
                # International
                "+00:00": "UTC",
                "+01:00": "Europe/London",     # GMT (winter) / BST (summer)
                "+02:00": "Europe/Paris",      # CET (winter) / CEST (summer)
                "+05:30": "Asia/Kolkata",      # IST (no DST)
                "+08:00": "Asia/Shanghai",     # CST (no DST)
                "+09:00": "Asia/Tokyo",        # JST (no DST)
            }
            
            # For conflicting offsets, we use the most common timezone
            # -05:00 could be EST or CDT, but EST is more common globally
            # -06:00 could be CST or MDT, but CST is more common
            # -07:00 could be MST or PDT, but MST is more common
            
            return offset_mappings.get(offset_str)
            
        except Exception as e:
            logger.error(f"Error converting offset to timezone: {e}")
            return None
    
    def _abbreviation_to_timezone(self, abbr: str) -> Optional[str]:
        """Convert timezone abbreviation to timezone name"""
        try:
            abbr_mappings = {
                "EST": "America/New_York",
                "EDT": "America/New_York",
                "CST": "America/Chicago",
                "CDT": "America/Chicago",
                "MST": "America/Denver",
                "MDT": "America/Denver",
                "PST": "America/Los_Angeles",
                "PDT": "America/Los_Angeles",
                "GMT": "Europe/London",
                "BST": "Europe/London",
                "CET": "Europe/Paris",
                "CEST": "Europe/Paris",
                "IST": "Asia/Kolkata",
                "JST": "Asia/Tokyo",
                "UTC": "UTC",
            }
            
            return abbr_mappings.get(abbr.upper())
            
        except Exception as e:
            logger.error(f"Error converting abbreviation to timezone: {e}")
            return None
    
    def _locale_to_timezone(self, locale: str) -> Optional[str]:
        """Convert locale to likely timezone"""
        try:
            locale_mappings = {
                "en_US": "America/New_York",
                "en_GB": "Europe/London",
                "fr_FR": "Europe/Paris",
                "de_DE": "Europe/Berlin",
                "ja_JP": "Asia/Tokyo",
                "zh_CN": "Asia/Shanghai",
                "en_IN": "Asia/Kolkata",
                "es_ES": "Europe/Madrid",
                "it_IT": "Europe/Rome",
                "pt_BR": "America/Sao_Paulo",
                "ru_RU": "Europe/Moscow",
                "ar_SA": "Asia/Riyadh",
            }
            
            return locale_mappings.get(locale)
            
        except Exception as e:
            logger.error(f"Error converting locale to timezone: {e}")
            return None
    
    def _parse_user_agent_timezone(self, user_agent: str) -> Optional[str]:
        """Parse user agent for timezone hints"""
        try:
            # This is a placeholder for potential user agent parsing
            # In practice, user agents rarely contain timezone information
            # Could potentially extract timezone from Accept-Language header patterns
            # or browser timezone APIs, but this is rarely available in WhatsApp context
            return None
            
        except Exception as e:
            logger.error(f"Error parsing user agent for timezone: {e}")
            return None
    
    async def update_user_timezone_from_message(self, user_id: str, message: Dict[str, Any], supabase_service) -> Optional[str]:
        """
        Update user's timezone based on phone data from their message
        This is the preferred method over IP detection
        
        Args:
            user_id: User ID
            message: WhatsApp message object with metadata
            supabase_service: Supabase service instance
            
        Returns:
            New timezone string or None if no update needed
        """
        try:
            # Get current stored timezone
            current_subscription = await supabase_service.get_subscription_by_id(user_id)
            current_timezone = current_subscription.get('current_timezone', 'UTC')
            
            # Try phone-based detection first (more accurate)
            detected_timezone = self.detect_timezone_from_phone(message)
            
            # Fallback to IP-based detection if available
            if not detected_timezone and message.get("client_ip"):
                detected_timezone = await self.detect_timezone_from_ip(message["client_ip"])
            
            # Only update if timezone has changed
            if detected_timezone and detected_timezone != current_timezone:
                logger.info(f"Timezone change detected for user {user_id}: {current_timezone} -> {detected_timezone}")
                
                # Update user's current timezone
                await supabase_service.update_subscription(
                    user_id, 
                    {
                        'current_timezone': detected_timezone,
                        'timezone_updated_at': 'now()'
                    }
                )
                
                return detected_timezone
            
            return None
            
        except Exception as e:
            logger.error(f"Error updating timezone for user {user_id}: {e}")
            return None