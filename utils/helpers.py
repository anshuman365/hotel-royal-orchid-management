import os
import secrets
from PIL import Image
from flask import current_app, url_for, request 
from functools import wraps
from flask_login import current_user
from flask import abort
from flask_wtf.csrf import validate_csrf
import requests

def save_picture(form_picture, folder='rooms'):
    """Save uploaded picture and return filename"""
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(current_app.root_path, 'static/uploads', folder, picture_fn)
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(picture_path), exist_ok=True)
    
    # Resize image
    output_size = (800, 600)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)
    
    return picture_fn

def admin_required(f):
    """Decorator to require admin privileges"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def staff_required(f):
    """Decorator to require staff privileges"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_staff():
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def csrf_protected(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.form.get('csrf_token')
        if not token or not validate_csrf(token):
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def format_currency(amount):
    """Format amount as Indian currency"""
    return f'₹{amount:,.2f}'

def format_date(date_obj):
    """Format date object as string"""
    return date_obj.strftime('%d %b %Y')

def get_room_image_url(room, size='medium'):
    """Get room image URL"""
    if room.images:
        try:
            images = eval(room.images)  # Convert string to list
            if images and len(images) > 0:
                return url_for('static', filename=f'uploads/rooms/{images[0]}')
        except:
            pass
    
    # Return default image if no images available
    return url_for('static', filename='images/room-placeholder.jpg')