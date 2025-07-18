"""
Tests for timezone offset mapping functionality in TimezoneService
"""

import pytest
from app.services.timezone_service import TimezoneService


class TestTimezoneOffsetMapping:
    """Test timezone offset to timezone name mapping with priority handling"""
    
    def setup_method(self):
        """Setup test instance"""
        self.timezone_service = TimezoneService()
    
    def test_primary_offset_mappings(self):
        """Test non-conflicting primary offset mappings"""
        test_cases = [
            ("-04:00", "America/New_York"),  # EDT
            ("-08:00", "America/Los_Angeles"),  # PST
            ("+00:00", "UTC"),
            ("+01:00", "Europe/London"),  # GMT/BST
            ("+02:00", "Europe/Paris"),  # CET/CEST
            ("+05:30", "Asia/Kolkata"),  # IST
            ("+08:00", "Asia/Shanghai"),  # CST
            ("+09:00", "Asia/Tokyo"),  # JST
        ]
        
        for offset, expected_timezone in test_cases:
            result = self.timezone_service._offset_to_timezone(offset)
            assert result == expected_timezone, f"Expected {expected_timezone} for offset {offset}, got {result}"
    
    def test_conflicting_offset_priority(self):
        """Test priority handling for conflicting timezone offsets"""
        # Test EST priority over CDT for -05:00
        result = self.timezone_service._offset_to_timezone("-05:00")
        assert result == "America/New_York", "EST should take priority over CDT for -05:00"
        
        # Test CST priority over MDT for -06:00
        result = self.timezone_service._offset_to_timezone("-06:00")
        assert result == "America/Chicago", "CST should take priority over MDT for -06:00"
        
        # Test MST priority over PDT for -07:00
        result = self.timezone_service._offset_to_timezone("-07:00")
        assert result == "America/Denver", "MST should take priority over PDT for -07:00"
    
    def test_invalid_offsets(self):
        """Test handling of invalid or unknown offsets"""
        invalid_offsets = [
            "+15:00",  # Out of valid range
            "-15:00",  # Out of valid range
            "+03:30",  # Valid but unmapped offset
            "invalid",  # Invalid format
            "",  # Empty string
            None,  # None value
        ]
        
        for offset in invalid_offsets:
            result = self.timezone_service._offset_to_timezone(offset)
            assert result is None, f"Expected None for invalid offset {offset}, got {result}"
    
    def test_edge_case_formats(self):
        """Test various offset format edge cases"""
        # These should all return None as they're not in our mapping
        edge_cases = [
            "+0000",  # No colon
            "+00",    # Missing minutes
            "00:00",  # Missing sign
            "+24:00", # Invalid hour
            "+00:60", # Invalid minute
        ]
        
        for offset in edge_cases:
            result = self.timezone_service._offset_to_timezone(offset)
            # Most of these should return None except maybe "+0000" if we handle it
            assert result is None or result == "UTC", f"Unexpected result for edge case {offset}: {result}"
    
    def test_abbreviation_to_timezone_mapping(self):
        """Test timezone abbreviation to timezone name mapping"""
        test_cases = [
            ("EST", "America/New_York"),
            ("EDT", "America/New_York"),
            ("CST", "America/Chicago"),
            ("CDT", "America/Chicago"),
            ("MST", "America/Denver"),
            ("MDT", "America/Denver"),
            ("PST", "America/Los_Angeles"),
            ("PDT", "America/Los_Angeles"),
            ("GMT", "Europe/London"),
            ("BST", "Europe/London"),
            ("CET", "Europe/Paris"),
            ("CEST", "Europe/Paris"),
            ("IST", "Asia/Kolkata"),
            ("JST", "Asia/Tokyo"),
            ("UTC", "UTC"),
        ]
        
        for abbr, expected_timezone in test_cases:
            result = self.timezone_service._abbreviation_to_timezone(abbr)
            assert result == expected_timezone, f"Expected {expected_timezone} for abbreviation {abbr}, got {result}"
    
    def test_case_insensitive_abbreviations(self):
        """Test that abbreviation mapping is case insensitive"""
        test_cases = [
            ("est", "America/New_York"),
            ("Est", "America/New_York"),
            ("EST", "America/New_York"),
            ("pst", "America/Los_Angeles"),
            ("Pst", "America/Los_Angeles"),
            ("PST", "America/Los_Angeles"),
        ]
        
        for abbr, expected_timezone in test_cases:
            result = self.timezone_service._abbreviation_to_timezone(abbr)
            assert result == expected_timezone, f"Expected {expected_timezone} for abbreviation {abbr}, got {result}"
    
    def test_unknown_abbreviations(self):
        """Test handling of unknown timezone abbreviations"""
        unknown_abbrs = ["XYZ", "ABC", "123", "", None]
        
        for abbr in unknown_abbrs:
            result = self.timezone_service._abbreviation_to_timezone(abbr)
            assert result is None, f"Expected None for unknown abbreviation {abbr}, got {result}"
    
    def test_locale_to_timezone_mapping(self):
        """Test locale to timezone mapping"""
        test_cases = [
            ("en_US", "America/New_York"),
            ("en_GB", "Europe/London"),
            ("fr_FR", "Europe/Paris"),
            ("de_DE", "Europe/Berlin"),
            ("ja_JP", "Asia/Tokyo"),
            ("zh_CN", "Asia/Shanghai"),
            ("en_IN", "Asia/Kolkata"),
            ("es_ES", "Europe/Madrid"),
            ("it_IT", "Europe/Rome"),
            ("pt_BR", "America/Sao_Paulo"),
            ("ru_RU", "Europe/Moscow"),
            ("ar_SA", "Asia/Riyadh"),
        ]
        
        for locale, expected_timezone in test_cases:
            result = self.timezone_service._locale_to_timezone(locale)
            assert result == expected_timezone, f"Expected {expected_timezone} for locale {locale}, got {result}"
    
    def test_unknown_locales(self):
        """Test handling of unknown locales"""
        unknown_locales = ["xx_XX", "invalid", "", None]
        
        for locale in unknown_locales:
            result = self.timezone_service._locale_to_timezone(locale)
            assert result is None, f"Expected None for unknown locale {locale}, got {result}"


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])