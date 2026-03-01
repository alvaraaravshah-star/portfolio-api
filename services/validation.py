"""
Validation Service Module
Handles request validation and date formatting.
"""

import re
from datetime import datetime
from typing import Tuple


class ValidationError(Exception):
    """Validation error."""
    pass


def validate_date_format(date_str: str) -> bool:
    """
    Validate that the date string is in YYYY-DD-MM format.
    
    Args:
        date_str: Date string to validate
    
    Returns:
        True if valid, False otherwise
    """
    if not isinstance(date_str, str):
        return False
    
    # expect four-digit year, two-digit day, two-digit month
    pattern = r"^\d{4}-\d{2}-\d{2}$"
    if not re.match(pattern, date_str):
        return False
    
    try:
        datetime.strptime(date_str, "%Y-%d-%m")
        return True
    except ValueError:
        return False


def validate_investor_type(investor_type: str) -> bool:
    """
    Validate investor type.
    
    Args:
        investor_type: Investor type string
    
    Returns:
        True if valid, False otherwise
    """
    valid_types = ["Conservative", "Balanced", "Aggressive"]
    return investor_type in valid_types


def validate_recommendation_request(target_date: str, investor_type: str) -> Tuple[bool, str]:
    """
    Validate a complete recommendation request.
    
    Args:
        target_date: Target date in YYYY-DD-MM format
        investor_type: Investor type
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not target_date:
        return False, "target_date is required"
    
    if not validate_date_format(target_date):
        return False, f"Invalid date format: {target_date}. Expected YYYY-DD-MM (e.g., 2009-01-04)"
    
    if not investor_type:
        return False, "investor_type is required"
    
    if not validate_investor_type(investor_type):
        valid_types = ["Conservative", "Balanced", "Aggressive"]
        return False, f"Invalid investor_type: {investor_type}. Must be one of: {', '.join(valid_types)}"
    
    return True, ""
