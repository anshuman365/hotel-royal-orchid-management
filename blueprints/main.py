from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import current_user, login_required
from app import db
from models.room import Room
from models.review import Review
from models.booking import Booking
from datetime import date

main_bp = Blueprint('main', __name__)

@main_bp.context_processor
def inject_today_date():
    return {'today': date.today().strftime('%Y-%m-%d')}

@main_bp.route('/')
def index():
    """Home page"""
    # Get featured rooms
    featured_rooms = Room.query.filter_by(status='available').limit(3).all()
    
    # Get approved reviews
    reviews = Review.query.filter_by(is_approved=True).order_by(Review.created_at.desc()).limit(6).all()
    
    return render_template('index.html', 
                         featured_rooms=featured_rooms,
                         reviews=reviews)

@main_bp.route('/rooms')
def rooms():
    """Rooms listing page"""
    room_type = request.args.get('type', '')
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    
    query = Room.query.filter_by(status='available')
    
    if room_type:
        query = query.filter_by(room_type=room_type)
    if min_price is not None:
        query = query.filter(Room.price >= min_price)
    if max_price is not None:
        query = query.filter(Room.price <= max_price)
    
    rooms = query.all()
    room_types = db.session.query(Room.room_type).distinct().all()
    
    return render_template('rooms.html', 
                         rooms=rooms,
                         room_types=[rt[0] for rt in room_types],
                         selected_type=room_type)

@main_bp.route('/room/<int:room_id>')
def room_detail(room_id):
    """Room detail page"""
    room = Room.query.get_or_404(room_id)
    reviews = Review.query.filter_by(room_id=room_id, is_approved=True).all()
    
    return render_template('room-detail.html', room=room, reviews=reviews)

@main_bp.route('/gallery')
def gallery():
    """Photo gallery page"""
    rooms = Room.query.filter_by(status='available').all()
    return render_template('gallery.html', rooms=rooms)

@main_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    """Contact page"""
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        subject = request.form.get('subject')
        message = request.form.get('message')
        
        # Here you would typically save to database and send email
        flash('Thank you for your message. We will get back to you soon!', 'success')
        return redirect(url_for('main.contact'))
    
    return render_template('contact.html')

@main_bp.route('/about')
def about():
    """About page"""
    return render_template('about.html')

@main_bp.route('/terms')
def terms():
    """Terms and conditions page"""
    return render_template('terms.html')

@main_bp.route('/privacy')
def privacy():
    """Privacy policy page"""
    return render_template('privacy.html')