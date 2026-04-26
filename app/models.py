from datetime import datetime, timezone
from . import db

class URL(db.Model):
    __tablename__ = 'urls'
    
    id = db.Column(db.Integer, primary_key=True)
    original_url = db.Column(db.String(2048), nullable=False, index=True) # Indexed for idempotency lookup
    short_code = db.Column(db.String(10), unique=True, nullable=False, index=True) # UNIQUE + INDEX for O(1) lookup
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = db.Column(db.DateTime, nullable=True)

    # Relationship to Analytics
    analytics = db.relationship('Analytics', backref='url', cascade='all, delete-orphan', uselist=False)

    def is_expired(self):
        if self.expires_at and datetime.now(timezone.utc) > self.expires_at.replace(tzinfo=timezone.utc):
            return True
        return False

class Analytics(db.Model):
    __tablename__ = 'analytics'
    
    id = db.Column(db.Integer, primary_key=True)
    url_id = db.Column(db.Integer, db.ForeignKey('urls.id'), nullable=False, unique=True)
    click_count = db.Column(db.Integer, default=0)
    last_accessed_at = db.Column(db.DateTime, nullable=True)
