from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, send_file
from flask_login import login_required, current_user
from app import db
from models.user import User
from models.room import Room
from models.booking import Booking
from models.payment import Payment
from models.review import Review
from models.offer import Offer
from datetime import datetime, date, timedelta
import csv
from io import BytesIO, TextIOWrapper
from io import StringIO
from utils.analytics_helpers import AnalyticsHelpers
import json
from utils.helpers import csrf_protected

api_bp = Blueprint('api', __name__)

@api_bp.route('/rooms/availability', methods=['GET'])
def check_availability():
    """Check room availability API"""
    check_in_str = request.args.get('check_in')
    check_out_str = request.args.get('check_out')
    guests = request.args.get('guests', 1, type=int)
    room_type = request.args.get('room_type')
    
    if not check_in_str or not check_out_str:
        return jsonify({'error': 'Check-in and check-out dates are required'}), 400
    
    try:
        check_in = datetime.strptime(check_in_str, '%Y-%m-%d').date()
        check_out = datetime.strptime(check_out_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
    
    # Validate dates
    if check_out <= check_in:
        return jsonify({'error': 'Check-out date must be after check-in date'}), 400
    
    # Build query
    query = Room.query.filter_by(status='available')
    
    if room_type:
        query = query.filter_by(room_type=room_type)
    
    if guests:
        query = query.filter(Room.capacity >= guests)
    
    all_rooms = query.all()
    
    # Filter available rooms
    available_rooms = []
    for room in all_rooms:
        if room.is_available(check_in, check_out):
            available_rooms.append(room.to_dict())
    
    return jsonify({
        'success': True,
        'available_rooms': available_rooms,
        'check_in': check_in_str,
        'check_out': check_out_str,
        'total_available': len(available_rooms)
    })

@api_bp.route('/booking/create', methods=['POST'])
def create_booking():
    """Create booking API"""
    data = request.get_json()
    
    required_fields = ['user_id', 'room_id', 'check_in', 'check_out', 'adults']
    for field in required_fields:
        if field not in data:
            return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400
    
    try:
        # Validate room exists and is available
        room = Room.query.get(data['room_id'])
        if not room:
            return jsonify({'success': False, 'error': 'Room not found'}), 404
        
        check_in = datetime.strptime(data['check_in'], '%Y-%m-%d').date()
        check_out = datetime.strptime(data['check_out'], '%Y-%m-%d').date()
        
        if not room.is_available(check_in, check_out):
            return jsonify({'success': False, 'error': 'Room not available for selected dates'}), 400
        
        # Calculate pricing
        nights = (check_out - check_in).days
        base_amount, tax_amount, total_amount = Booking().calculate_total_amount(room.price)
        final_amount = total_amount
        
        # Apply coupon if provided
        discount_amount = 0
        coupon_code = data.get('coupon_code')
        if coupon_code:
            offer = Offer.query.filter_by(code=coupon_code).first()
            if offer and offer.is_valid():
                discount_amount = offer.calculate_discount(total_amount)
                final_amount = total_amount - discount_amount
        
        # Create booking
        booking = Booking(
            user_id=data['user_id'],
            room_id=data['room_id'],
            check_in=check_in,
            check_out=check_out,
            adults=data['adults'],
            children=data.get('children', 0),
            total_nights=nights,
            base_amount=base_amount,
            tax_amount=tax_amount,
            discount_amount=discount_amount,
            total_amount=total_amount,
            final_amount=final_amount,
            coupon_code=coupon_code,
            special_requests=data.get('special_requests', ''),
            status='pending'
        )
        
        db.session.add(booking)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'booking_id': booking.id,
            'message': 'Booking created successfully',
            'booking': booking.to_dict()
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/offers/validate', methods=['POST'])
def validate_offer():
    """Validate coupon code API"""
    data = request.get_json()
    coupon_code = data.get('coupon_code')
    total_amount = float(data.get('total_amount', 0))
    
    if not coupon_code:
        return jsonify({'success': False, 'error': 'Coupon code is required'}), 400
    
    offer = Offer.query.filter_by(code=coupon_code).first()
    
    if not offer:
        return jsonify({'success': False, 'error': 'Invalid coupon code'}), 404
    
    if not offer.is_valid():
        return jsonify({'success': False, 'error': 'Coupon code has expired'}), 400
    
    if total_amount < offer.min_amount:
        return jsonify({
            'success': False, 
            'error': f'Minimum amount required: ₹{offer.min_amount:.2f}'
        }), 400
    
    discount = offer.calculate_discount(total_amount)
    final_amount = total_amount - discount
    
    return jsonify({
        'success': True,
        'discount': discount,
        'final_amount': final_amount,
        'offer': offer.to_dict()
    })

@api_bp.route('/rooms/<int:room_id>', methods=['GET'])
def get_room_details(room_id):
    """Get room details API"""
    room = Room.query.get(room_id)
    
    if not room:
        return jsonify({'success': False, 'error': 'Room not found'}), 404
    
    return jsonify({
        'success': True,
        'room': room.to_dict()
    })

@api_bp.route('/dashboard/stats', methods=['GET'])
def dashboard_stats():
    """Get dashboard statistics API"""
    from datetime import date, timedelta
    
    # Basic counts
    total_rooms = Room.query.count()
    available_rooms = Room.query.filter_by(status='available').count()
    total_bookings = Booking.query.count()
    pending_bookings = Booking.query.filter_by(status='pending').count()
    
    # Today's stats
    today = date.today()
    today_checkins = Booking.query.filter_by(check_in=today, status='confirmed').count()
    today_checkouts = Booking.query.filter_by(check_out=today, status='confirmed').count()
    
    # Revenue (last 30 days)
    thirty_days_ago = today - timedelta(days=30)
    from models.payment import Payment
    recent_payments = Payment.query.filter(
        Payment.payment_status == 'completed',
        Payment.created_at >= thirty_days_ago
    ).all()
    
    total_revenue = sum(p.amount for p in recent_payments)
    
    return jsonify({
        'success': True,
        'stats': {
            'total_rooms': total_rooms,
            'available_rooms': available_rooms,
            'total_bookings': total_bookings,
            'pending_bookings': pending_bookings,
            'today_checkins': today_checkins,
            'today_checkouts': today_checkouts,
            'total_revenue': total_revenue
        }
    })

@api_bp.route('/admin/metrics/live')
@login_required
def admin_live_metrics():
    """Get live metrics for admin chatbot"""
    try:
        # Current occupancy
        today = datetime.utcnow().date()
        occupied_rooms = Booking.query.filter(
            Booking.check_in <= today,
            Booking.check_out > today,
            Booking.status.in_(['confirmed', 'checked_in'])
        ).count()
        
        total_rooms = Room.query.count()
        occupancy_rate = (occupied_rooms / total_rooms * 100) if total_rooms > 0 else 0
        
        # Today's revenue
        today_revenue = db.session.query(db.func.sum(Payment.amount)).filter(
            db.func.date(Payment.created_at) == today,
            Payment.payment_status == 'completed'
        ).scalar() or 0
        
        # Today's bookings
        today_bookings = Booking.query.filter(
            db.func.date(Booking.created_at) == today
        ).count()
        
        # Alerts
        alerts = []
        if occupancy_rate < 30:
            alerts.append({
                'title': 'Low Occupancy',
                'message': f'Current occupancy is only {occupancy_rate:.1f}%',
                'type': 'warning'
            })
        
        pending_reviews = Review.query.filter_by(is_approved=False).count()
        if pending_reviews > 5:
            alerts.append({
                'title': 'Review Backlog',
                'message': f'{pending_reviews} reviews pending approval',
                'type': 'warning'
            })
        
        return jsonify({
            'success': True,
            'occupancy': round(occupancy_rate, 1),
            'revenue': today_revenue,
            'bookings': today_bookings,
            'alerts': alerts
        })
        
    except Exception as e:
        print(f"Error getting live metrics: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to load metrics'
        })

@api_bp.route('/admin/chat/history')
@login_required
def admin_chat_history():
    """Get admin chat history"""
    # For now, return empty history - you can implement proper chat storage later
    return jsonify({
        'success': True,
        'history': []
    })

# Update the admin_chat_send route in admin.py
@api_bp.route('/admin/chat/send', methods=['POST'])
@login_required
def admin_chat_send():
    """Handle admin chat messages"""
    try:
        data = request.get_json()
        message = data.get('message', '').strip()
        
        if not message:
            return jsonify({'success': False, 'error': 'Empty message'})
        
        # Use AdminAIService for business context responses
        from utils.ai_service import AdminAIService
        admin_ai = AdminAIService()
        
        # Get AI response with business context
        try:
            response = admin_ai.chat_with_business_context(message, current_user)
        except Exception as e:
            print(f"AI service failed, using fallback: {e}")
            response = admin_ai._get_admin_fallback_response(message)
        
        return jsonify({
            'success': True,
            'response': response,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        print(f"Admin chat error: {e}")
        # Even if everything fails, return a basic fallback
        from utils.ai_service import AdminAIService
        admin_ai = AdminAIService()
        fallback_response = admin_ai._get_admin_fallback_response(message)
        
        return jsonify({
            'success': True,
            'response': fallback_response,
            'timestamp': datetime.utcnow().isoformat(),
            'note': 'Using fallback response due to system issues'
        })

@api_bp.route('/admin/chat/clear', methods=['POST'])
@login_required
def admin_chat_clear():
    """Clear admin chat history"""
    # In a real implementation, you'd clear from database
    return jsonify({'success': True})

@api_bp.route('/admin/chat/generate-report', methods=['POST'])
@login_required
def admin_generate_report():
    """Generate business report"""
    try:
        data = request.get_json()
        report_type = data.get('report_type', 'comprehensive')
        
        from utils.ai_service import AdminAIService
        admin_ai = AdminAIService()
        
        report = admin_ai.generate_business_report(report_type)
        
        return jsonify({
            'success': True,
            'report': report,
            'generated_at': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        print(f"Report generation error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to generate report'
        })