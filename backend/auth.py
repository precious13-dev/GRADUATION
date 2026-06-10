# backend/auth.py
import jwt, datetime, functools
from flask import request, jsonify
import hashlib, hmac

SECRET  = 'GPMS_CUZ_SECRET_CHANGE_IN_PROD'
EXPIRY  = 8  # hours

def create_token(user: dict) -> str:
    payload = {
        'id':    user['id'],
        'name':  user['name'],
        'email': user['email'],
        'role':  user['role'],
        'exp':   datetime.datetime.utcnow() + datetime.timedelta(hours=EXPIRY),
    }
    return jwt.encode(payload, SECRET, algorithm='HS256')

def create_signed_url(doc_id: int, user_id: int, expires_in_seconds: int = 60) -> tuple:
    """
    Generate a signed URL for temporary file access.
    Returns: (token, expiry_timestamp)
    Token format: doc_id:user_id:expiry:signature
    """
    expiry = datetime.datetime.utcnow() + datetime.timedelta(seconds=expires_in_seconds)
    expiry_unix = int(expiry.timestamp())
    
    # Create signature: HMAC-SHA256 of doc_id:user_id:expiry
    message = f"{doc_id}:{user_id}:{expiry_unix}".encode()
    signature = hmac.new(SECRET.encode(), message, hashlib.sha256).hexdigest()
    
    token = f"{doc_id}:{user_id}:{expiry_unix}:{signature}"
    return token, expiry_unix

def verify_signed_url(token: str) -> dict | None:
    """
    Verify and parse a signed URL token.
    Returns: {'doc_id': int, 'user_id': int} or None if invalid/expired
    """
    try:
        parts = token.split(':')
        if len(parts) != 4:
            return None
        
        doc_id, user_id, expiry_unix, signature = parts
        doc_id, user_id, expiry_unix = int(doc_id), int(user_id), int(expiry_unix)
        
        # Check expiry
        if datetime.datetime.utcnow().timestamp() > expiry_unix:
            return None
        
        # Verify signature
        message = f"{doc_id}:{user_id}:{expiry_unix}".encode()
        expected_sig = hmac.new(SECRET.encode(), message, hashlib.sha256).hexdigest()
        
        if not hmac.compare_digest(signature, expected_sig):
            return None
        
        return {'doc_id': doc_id, 'user_id': user_id}
    except (ValueError, IndexError):
        return None

def decode_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, SECRET, algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def get_token_from_request() -> str | None:
    auth = request.headers.get('Authorization', '')
    if auth.startswith('Bearer '):
        return auth[7:]
    # Check query parameter for iframe requests
    token = request.args.get('token')
    if token:
        return token
    return None

def require_auth(allowed_roles=None):
    """Decorator — protects a route. Pass a list of allowed roles, or None for any."""
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            token = get_token_from_request()
            if not token:
                return jsonify({'success': False, 'message': 'Unauthorized: No token provided'}), 401

            payload = decode_token(token)
            if not payload:
                return jsonify({'success': False, 'message': 'Unauthorized: Invalid or expired token'}), 401

            if allowed_roles and payload['role'] not in allowed_roles:
                return jsonify({'success': False, 'message': 'Forbidden: Insufficient permissions'}), 403

            request.user = payload
            return fn(*args, **kwargs)
        return wrapper
    return decorator
