import re
from typing import Optional, Tuple
import phonenumbers
from phonenumbers import NumberParseException, PhoneNumberFormat


def normalize_indian_phone(raw_phone: str) -> Tuple[bool, str, Optional[str]]:
    """
    Normalizes an input phone number to canonical E.164 format (+91XXXXXXXXXX).
    Handles:
    - Standard 10-digit: 9825158210 -> +919825158210
    - Leading zero: 09825158210 -> +919825158210
    - With country code: +91 98251 58210 -> +919825158210
    - Formatted dashes/spaces: +91-98251-58210 -> +919825158210
    Returns:
    (is_valid: bool, normalized_phone: str, error_message: Optional[str])
    """
    if not raw_phone:
        return False, "", "Phone number cannot be empty"

    cleaned = re.sub(r"[^\d+]", "", raw_phone.strip())
    
    # If standard 10 digits starting with 6, 7, 8, or 9
    if len(cleaned) == 10 and cleaned[0] in "6789":
        cleaned = "+91" + cleaned
    elif len(cleaned) == 11 and cleaned.startswith("0") and cleaned[1] in "6789":
        cleaned = "+91" + cleaned[1:]
    elif len(cleaned) == 12 and cleaned.startswith("91") and cleaned[2] in "6789":
        cleaned = "+" + cleaned

    try:
        parsed = phonenumbers.parse(cleaned, "IN")
        if phonenumbers.is_valid_number(parsed):
            formatted = phonenumbers.format_number(parsed, PhoneNumberFormat.E164)
            return True, formatted, None
        else:
            return False, raw_phone, "Invalid Indian phone number format"
    except NumberParseException:
        # Fallback regex check for 10-digit Indian mobile
        digits_only = re.sub(r"\D", "", raw_phone)
        if len(digits_only) == 10 and digits_only[0] in "6789":
            return True, f"+91{digits_only}", None
        if len(digits_only) == 12 and digits_only.startswith("91") and digits_only[2] in "6789":
            return True, f"+{digits_only}", None
        return False, raw_phone, "Unable to parse phone number"
