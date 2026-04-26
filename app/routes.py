from flask import Blueprint, request, jsonify, redirect, render_template
from .models import URL, Analytics, db
from .services import get_or_create_short_url, increment_click_count
from .utils import validate_url, sanitize_url, format_error
from datetime import datetime, timezone, timedelta

bp = Blueprint('api', __name__)

@bp.route('/')
def index():
    return render_template('index.html')

@bp.route('/shorten', methods=['POST'])
def shorten():
    data = request.get_json()
    if not data or 'url' not in data:
        return format_error("Missing URL parameter", 400)

    original_url = sanitize_url(data.get('url'))
    if not validate_url(original_url):
        return format_error("Invalid URL format", 400)

    # Optional expiration
    expires_in_days = data.get('expires_in_days')
    expires_at = None
    if expires_in_days:
        try:
            expires_at = datetime.now(timezone.utc) + timedelta(days=float(expires_in_days))
        except (ValueError, TypeError):
            return format_error("Invalid expiration period", 400)

    url_obj, created = get_or_create_short_url(original_url, expires_at)
    
    status_code = 201 if created else 200
    return jsonify({
        "short_code": url_obj.short_code,
        "short_url": request.host_url + url_obj.short_code,
        "original_url": url_obj.original_url,
        "expires_at": url_obj.expires_at.isoformat() if url_obj.expires_at else None,
        "created": created
    }), status_code

@bp.route('/<short_code>')
def redirect_to_url(short_code):
    # Optimized indexed lookup
    url_obj = URL.query.filter_by(short_code=short_code).first()
    
    if not url_obj:
        return format_error("Short code not found", 404)
    
    if url_obj.is_expired():
        return format_error("This link has expired", 410)
    
    # Atomic analytics update
    increment_click_count(url_obj.id)
    
    return redirect(url_obj.original_url, code=302)

@bp.route('/analytics/<short_code>')
def get_analytics(short_code):
    url_obj = URL.query.filter_by(short_code=short_code).first()
    
    if not url_obj:
        return format_error("Short code not found", 404)
    
    analytics = Analytics.query.filter_by(url_id=url_obj.id).first()
    
    return jsonify({
        "short_code": url_obj.short_code,
        "original_url": url_obj.original_url,
        "click_count": analytics.click_count if analytics else 0,
        "last_accessed_at": analytics.last_accessed_at.isoformat() if analytics and analytics.last_accessed_at else None,
        "created_at": url_obj.created_at.isoformat()
    }), 200
