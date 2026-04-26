import re
import validators
from urllib.parse import urlparse

def validate_url(url):
    """
    Validates the URL format and ensures it has a scheme and netloc.
    """
    if not url:
        return False
    
    # Basic format check using validators
    if not validators.url(url):
        return False
    
    parsed = urlparse(url)
    return bool(parsed.scheme and parsed.netloc)

def sanitize_url(url):
    """
    Basic sanitization to strip whitespace and potentially dangerous characters.
    """
    if not url:
        return ""
    return url.strip()

def format_error(message, status_code):
    """
    Standardizes error responses.
    """
    return {"error": message, "status": status_code}, status_code
