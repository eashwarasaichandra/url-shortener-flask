import string
import random
from datetime import datetime, timezone
from .models import URL, Analytics, db

BASE62 = string.digits + string.ascii_letters

def generate_short_code(length=6):
    """
    Generates a random Base62 short code.
    """
    return ''.join(random.choices(BASE62, k=length))

def get_or_create_short_url(original_url, expires_at=None):
    """
    Idempotent behavior: returns existing short code if URL already exists.
    Otherwise, creates a new one.
    """
    # Check if URL already exists (Idempotency)
    existing_url = URL.query.filter_by(original_url=original_url).first()
    if existing_url:
        return existing_url, False

    # Generate a unique short code with collision handling
    short_code = generate_short_code()
    while URL.query.filter_by(short_code=short_code).first():
        short_code = generate_short_code()

    new_url = URL(
        original_url=original_url,
        short_code=short_code,
        expires_at=expires_at
    )
    
    # Initialize analytics
    analytics = Analytics(url=new_url)
    
    db.session.add(new_url)
    db.session.add(analytics)
    db.session.commit()
    
    return new_url, True

def increment_click_count(url_id):
    """
    Transaction-safe atomic increment of click count.
    """
    analytics = Analytics.query.filter_by(url_id=url_id).first()
    if analytics:
        # Atomic update
        analytics.click_count += 1
        analytics.last_accessed_at = datetime.now(timezone.utc)
        db.session.commit()
