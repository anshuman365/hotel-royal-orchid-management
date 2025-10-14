# © 2025 Anshuman Singh. All Rights Reserved.
# Unauthorized use prohibited.
import re
from flask import current_app
from itsdangerous import URLSafeTimedSerializer
from werkzeug.security import check_password_hash, generate_password_hash

def generate_password_strength(password):
    """Check password strength"""
    if len(password) < 8:
        return "weak", "Password must be at least 8 characters long"
    
    if not re.search(r"[A-Z]", password):
        return "weak", "Password must contain at least one uppercase letter"
    
    if not re.search(r"[a-z]", password):
        return "weak", "Password must contain at least one lowercase letter"
    
    if not re.search(r"\d", password):
        return "weak", "Password must contain at least one number"
    
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return "medium", "Consider adding special characters for stronger password"
    
    return "strong", "Password is strong"

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone):
    """Validate Indian phone number"""
    pattern = r'^[6-9]\d{9}$'
    return re.match(pattern, phone) is not None

def generate_confirmation_token(email):
    """Generate email confirmation token"""
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return serializer.dumps(email, salt='email-confirm-salt')

def confirm_token(token, expiration=3600):
    """Confirm email confirmation token"""
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = serializer.loads(
            token,
            salt='email-confirm-salt',
            max_age=expiration
        )
        return email
    except:
        return False

def sanitize_input(text):
    """Sanitize user input to prevent XSS"""
    if not text:
        return text
    
    # Basic XSS prevention
    sanitized = text.replace('<', '&lt;').replace('>', '&gt;')
    sanitized = sanitized.replace('"', '&quot;').replace("'", '&#x27;')
    
    return sanitized