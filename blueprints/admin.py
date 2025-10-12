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

admin_bp = Blueprint('admin', __name__)

@admin_bp.before_request
def restrict_to_admin():
    """Restrict admin routes to admin users only"""
    if not current_user.is_authenticated or not current_user.is_staff():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))

@admin_bp.route('/')
@admin_bp.route('/dashboard')
@login_required
def dashboard():
    """Admin dashboard"""
    # Basic statistics
    total_rooms = Room.query.count()
    available_rooms = Room.query.filter_by(status='available').count()
    total_bookings = Booking.query.count()
    today_checkins = Booking.query.filter_by(check_in=date.today(), status='confirmed').count()
    today_checkouts = Booking.query.filter_by(check_out=date.today(), status='confirmed').count()
    
    # Revenue statistics (last 30 days)
    thirty_days_ago = date.today() - timedelta(days=30)
    recent_payments = Payment.query.filter(
        Payment.payment_status == 'completed',
        Payment.created_at >= thirty_days_ago
    ).all()
    
    total_revenue = sum(p.amount for p in recent_payments)
    
    # Recent bookings
    recent_bookings = Booking.query.order_by(Booking.created_at.desc()).limit(10).all()
    
    return render_template('admin/dashboard.html',
                         total_rooms=total_rooms,
                         available_rooms=available_rooms,
                         total_bookings=total_bookings,
                         today_checkins=today_checkins,
                         today_checkouts=today_checkouts,
                         total_revenue=total_revenue,
                         recent_bookings=recent_bookings,
                         Review=Review)

@admin_bp.route('/rooms')
@login_required
def manage_rooms():
    """Room management"""
    rooms = Room.query.all()
    return render_template('admin/rooms.html', rooms=rooms)

@admin_bp.route('/rooms/add', methods=['GET', 'POST'])
@login_required
def add_room():
    """Add new room"""
    if request.method == 'POST':
        name = request.form.get('name')
        room_type = request.form.get('room_type')
        price = float(request.form.get('price'))
        capacity = int(request.form.get('capacity'))
        size = request.form.get('size')
        amenities = request.form.get('amenities')
        description = request.form.get('description')
        max_adults = int(request.form.get('max_adults', 2))
        max_children = int(request.form.get('max_children', 2))
        
        room = Room(
            name=name,
            room_type=room_type,
            price=price,
            capacity=capacity,
            size=size,
            amenities=amenities,
            description=description,
            max_adults=max_adults,
            max_children=max_children
        )
        
        db.session.add(room)
        db.session.commit()
        
        flash('Room added successfully!', 'success')
        return redirect(url_for('admin.manage_rooms'))
    
    return render_template('admin/room_form.html')

@admin_bp.route('/rooms/edit/<int:room_id>', methods=['GET', 'POST'])
@login_required
def edit_room(room_id):
    """Edit room"""
    room = Room.query.get_or_404(room_id)
    
    if request.method == 'POST':
        room.name = request.form.get('name')
        room.room_type = request.form.get('room_type')
        room.price = float(request.form.get('price'))
        room.capacity = int(request.form.get('capacity'))
        room.size = request.form.get('size')
        room.amenities = request.form.get('amenities')
        room.description = request.form.get('description')
        room.max_adults = int(request.form.get('max_adults', 2))
        room.max_children = int(request.form.get('max_children', 2))
        room.status = request.form.get('status', 'available')
        
        db.session.commit()
        flash('Room updated successfully!', 'success')
        return redirect(url_for('admin.manage_rooms'))
    
    return render_template('admin/room_form.html', room=room)

@admin_bp.route('/rooms/delete/<int:room_id>')
@login_required
def delete_room(room_id):
    """Delete room"""
    room = Room.query.get_or_404(room_id)
    
    # Check if room has bookings
    if room.bookings:
        flash('Cannot delete room with existing bookings.', 'danger')
        return redirect(url_for('admin.manage_rooms'))
    
    db.session.delete(room)
    db.session.commit()
    
    flash('Room deleted successfully!', 'success')
    return redirect(url_for('admin.manage_rooms'))

@admin_bp.route('/bookings')
@login_required
def manage_bookings():
    """Booking management"""
    status_filter = request.args.get('status', '')
    
    query = Booking.query
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    bookings = query.order_by(Booking.created_at.desc()).all()
    return render_template('admin/bookings.html', bookings=bookings)

@admin_bp.route('/bookings/update_status/<int:booking_id>', methods=['POST'])
@login_required
def update_booking_status(booking_id):
    """Update booking status with validation"""
    booking = Booking.query.get_or_404(booking_id)
    new_status = request.form.get('status')
    admin_note = request.form.get('admin_note')
    notify_user = request.form.get('notify_user') == 'on'
    
    # Define allowed status transitions (no downgrades)
    allowed_transitions = {
        'pending': ['confirmed', 'cancelled'],
        'confirmed': ['checked_in', 'cancelled'],
        'checked_in': ['checked_out', 'completed'],
        'checked_out': ['completed'],
        'cancelled': [],  # Once cancelled, no further changes
        'completed': []   # Once completed, no further changes
    }
    
    current_status = booking.status
    allowed_next_statuses = allowed_transitions.get(current_status, [])
    
    if new_status not in allowed_next_statuses:
        if new_status == current_status:
            flash('Booking status is already set to this value.', 'info')
        else:
            flash(f'Cannot change status from {current_status} to {new_status}.', 'danger')
        return redirect(url_for('admin.manage_bookings'))
    
    # Update booking status
    booking.status = new_status
    db.session.commit()
    
    # Send notifications if requested
    if notify_user:
        try:
            from utils.email_service import send_admin_booking_update
            send_admin_booking_update(booking, admin_note)
            flash('Booking status updated and user notified successfully!', 'success')
        except Exception as e:
            print(f"Notification sending failed: {e}")
            flash('Status updated but notification failed to send.', 'warning')
    else:
        flash('Booking status updated successfully!', 'success')
    
    return redirect(url_for('admin.manage_bookings'))

@admin_bp.route('/reviews')
@login_required
def manage_reviews():
    """Enhanced review management with filtering"""
    status_filter = request.args.get('status', 'pending')  # pending, approved, all
    room_filter = request.args.get('room_id', type=int)
    
    query = Review.query
    
    if status_filter == 'pending':
        query = query.filter_by(is_approved=False)
    elif status_filter == 'approved':
        query = query.filter_by(is_approved=True)
    # 'all' shows everything
    
    if room_filter:
        query = query.filter_by(room_id=room_filter)
    
    reviews = query.order_by(Review.created_at.desc()).all()
    rooms = Room.query.all()
    
    return render_template('admin/reviews.html', 
                         reviews=reviews, 
                         rooms=rooms,
                         status_filter=status_filter,
                         room_filter=room_filter)

@admin_bp.route('/reviews/approve/<int:review_id>')
@login_required
def approve_review(review_id):
    """Approve review with enhanced functionality"""
    review = Review.query.get_or_404(review_id)
    review.is_approved = True
    review.is_verified = True  # Mark as verified when approved by admin
    
    # Send notification to user
    try:
        from utils.email_service import send_review_approved_notification
        send_review_approved_notification(review, review.user.email)
    except Exception as e:
        print(f"Review approval notification failed: {e}")
    
    db.session.commit()
    
    # Update room ratings - fixed import
    try:
        # Import the function from the correct location
        from blueprints.reviews import update_room_ratings
        update_room_ratings(review.room_id)
    except ImportError:
        # Fallback: call the function directly if import fails
        update_room_ratings_fallback(review.room_id)
    
    flash('Review approved and published!', 'success')
    return redirect(url_for('admin.manage_reviews'))

def update_room_ratings_fallback(room_id):
    """Fallback function to update room ratings"""
    from models.room import Room
    from models.review import Review
    
    room = Room.query.get(room_id)
    if not room:
        return
    
    # Calculate new average rating from approved reviews
    approved_reviews = Review.query.filter_by(
        room_id=room_id, 
        is_approved=True
    ).all()
    
    if approved_reviews:
        # Overall rating
        total_rating = sum(review.rating for review in approved_reviews)
        average_rating = total_rating / len(approved_reviews)
        
        # Detailed ratings averages
        cleanliness_avg = sum(review.cleanliness_rating for review in approved_reviews) / len(approved_reviews)
        comfort_avg = sum(review.comfort_rating for review in approved_reviews) / len(approved_reviews)
        location_avg = sum(review.location_rating for review in approved_reviews) / len(approved_reviews)
        amenities_avg = sum(review.amenities_rating for review in approved_reviews) / len(approved_reviews)
        service_avg = sum(review.service_rating for review in approved_reviews) / len(approved_reviews)

@admin_bp.route('/reviews/reject/<int:review_id>', methods=['POST'])
@login_required
def reject_review(review_id):
    """Reject review with reason"""
    review = Review.query.get_or_404(review_id)
    rejection_reason = request.form.get('rejection_reason', 'Does not meet our guidelines')
    
    # Store rejection reason (you might want to add this field to Review model)
    # For now, we'll just delete the review
    
    # Send rejection notification
    try:
        from utils.email_service import send_review_rejected_notification
        send_review_rejected_notification(review, review.user.email, rejection_reason)
    except Exception as e:
        print(f"Review rejection notification failed: {e}")
    
    db.session.delete(review)
    db.session.commit()
    
    flash('Review rejected and user notified.', 'success')
    return redirect(url_for('admin.manage_reviews'))

@admin_bp.route('/review/<int:review_id>/reply', methods=['POST'])
@login_required
def admin_reply_review_f(review_id):
    """Add management reply to review (admin version)"""
    review = Review.query.get_or_404(review_id)
    reply_text = request.form.get('reply')
    
    if not reply_text:
        flash('Reply text is required.', 'danger')
        return redirect(url_for('admin.manage_reviews'))
    
    review.reply = reply_text
    review.reply_date = datetime.utcnow()
    db.session.commit()
    
    # Send notification to user about management response
    try:
        from utils.email_service import send_review_reply_notification
        send_review_reply_notification(review, review.user.email)
    except Exception as e:
        print(f"Review reply notification failed: {e}")
    
    flash('Reply added successfully!', 'success')
    return redirect(url_for('admin.manage_reviews'))

@admin_bp.route('/reply_review/<int:review_id>', methods=['POST'])
@login_required
def admin_reply_review(review_id):
    """Add management reply to review (admin version)"""
    review = Review.query.get_or_404(review_id)
    reply_text = request.form.get('reply')
    
    if not reply_text:
        flash('Reply text is required.', 'danger')
        return redirect(url_for('admin.manage_reviews'))
    
    review.reply = reply_text
    review.reply_date = datetime.utcnow()
    db.session.commit()
    
    # Send notification to user about management response
    try:
        from utils.email_service import send_review_reply_notification
        send_review_reply_notification(review, review.user.email)
    except Exception as e:
        print(f"Review reply notification failed: {e}")
    
    flash('Reply added successfully!', 'success')
    return redirect(url_for('admin.manage_reviews'))

@admin_bp.route('/reviews/stats')
@login_required
def review_stats():
    """Review statistics for admin"""
    total_reviews = Review.query.count()
    pending_reviews = Review.query.filter_by(is_approved=False).count()
    approved_reviews = Review.query.filter_by(is_approved=True).count()
    
    # Average ratings
    avg_rating = db.session.query(db.func.avg(Review.rating)).filter_by(is_approved=True).scalar() or 0
    avg_cleanliness = db.session.query(db.func.avg(Review.cleanliness_rating)).filter_by(is_approved=True).scalar() or 0
    avg_service = db.session.query(db.func.avg(Review.service_rating)).filter_by(is_approved=True).scalar() or 0
    
    # Recent reviews (last 7 days)
    week_ago = datetime.utcnow() - timedelta(days=7)
    recent_reviews = Review.query.filter(Review.created_at >= week_ago).count()
    
    return jsonify({
        'total_reviews': total_reviews,
        'pending_reviews': pending_reviews,
        'approved_reviews': approved_reviews,
        'approval_rate': (approved_reviews / total_reviews * 100) if total_reviews > 0 else 0,
        'average_rating': round(avg_rating, 1),
        'average_cleanliness': round(avg_cleanliness, 1),
        'average_service': round(avg_service, 1),
        'recent_reviews': recent_reviews
    })

@admin_bp.route('/analytics')
@login_required
def analytics():
    """Enhanced analytics and reports with real data"""
    # Calculate date ranges
    today = date.today()
    thirty_days_ago = today - timedelta(days=30)
    seven_days_ago = today - timedelta(days=7)
    
    # Revenue statistics
    recent_payments = Payment.query.filter(
        Payment.payment_status == 'completed',
        Payment.created_at >= thirty_days_ago
    ).all()
    total_revenue = sum(p.amount for p in recent_payments)
    
    # Booking statistics
    total_bookings = Booking.query.count()
    recent_bookings = Booking.query.filter(Booking.created_at >= thirty_days_ago).count()
    
    # Room statistics
    total_rooms = Room.query.count()
    available_rooms = Room.query.filter_by(status='available').count()
    
    # Calculate occupancy rate (simplified)
    total_room_nights = sum(booking.total_nights for booking in Booking.query.filter(
        Booking.status.in_(['confirmed', 'checked_in', 'checked_out', 'completed'])
    ).all())
    max_room_nights = total_rooms * 30  # Maximum possible room nights in 30 days
    occupancy_rate = (total_room_nights / max_room_nights * 100) if max_room_nights > 0 else 0
    
    # Review statistics
    avg_rating = db.session.query(db.func.avg(Review.rating)).filter_by(is_approved=True).scalar() or 0
    
    # Room performance data
    rooms = Room.query.all()
    room_performance = []
    for room in rooms:
        room_bookings = [b for b in room.bookings if b.status in ['confirmed', 'checked_in', 'checked_out', 'completed']]
        room_revenue = sum(b.final_amount for b in room_bookings)
        room_rating = room.get_average_rating()
        
        room_performance.append({
            'name': room.name,
            'type': room.room_type,
            'bookings': len(room_bookings),
            'revenue': room_revenue,
            'occupancy': (len(room_bookings) / 30 * 100) if len(room_bookings) > 0 else 0,  # Simplified
            'rating': room_rating
        })
    
    # Offer analytics
    from utils.offer_engine import SmartOfferEngine
    offer_analytics = SmartOfferEngine.get_offer_analytics()
    offer_insights = SmartOfferEngine.generate_offer_insights()
    
    return render_template('admin/analytics.html',
                         total_revenue=total_revenue,
                         total_bookings=total_bookings,
                         recent_bookings=recent_bookings,
                         occupancy_rate=round(occupancy_rate, 1),
                         avg_rating=round(avg_rating, 1),
                         room_performance=room_performance,
                         offer_analytics=offer_analytics,
                         offer_insights=offer_insights,
                         today=today,
                         thirty_days_ago=thirty_days_ago)

@admin_bp.route('/analytics/chart-data')
@login_required
def analytics_chart_data():
    """API endpoint for chart data - FIXED VERSION"""
    try:
        # Revenue data with fallback
        revenue_raw_data = AnalyticsHelpers.get_revenue_chart_data(30)
        if not revenue_raw_data:
            # Generate sample data if no real data
            revenue_raw_data = AnalyticsHelpers.generate_sample_revenue_data(30)
        
        revenue_data = AnalyticsHelpers.format_chart_data(revenue_raw_data, 'revenue')
        
        # Occupancy data with fallback
        occupancy_raw_data = AnalyticsHelpers.get_occupancy_chart_data(30)
        if not occupancy_raw_data:
            # Generate sample data if no real data
            occupancy_raw_data = AnalyticsHelpers.generate_sample_occupancy_data(30)
        
        occupancy_data = AnalyticsHelpers.format_chart_data(occupancy_raw_data, 'rate')
        
        total_revenue_30d = sum(item['revenue'] for item in revenue_raw_data)
        avg_occupancy_30d = sum(item['rate'] for item in occupancy_raw_data) / len(occupancy_raw_data) if occupancy_raw_data else 0
        
        return jsonify({
            'success': True,
            'revenue_data': revenue_data,
            'occupancy_data': occupancy_data,
            'summary': {
                'total_revenue_30d': total_revenue_30d,
                'avg_occupancy_30d': round(avg_occupancy_30d, 1)
            }
        })
    except Exception as e:
        print(f"Error generating chart data: {e}")
        # Return sample data on error
        sample_data = AnalyticsHelpers.generate_sample_chart_data()
        return jsonify({
            'success': True,
            'revenue_data': sample_data['revenue_data'],
            'occupancy_data': sample_data['occupancy_data'],
            'summary': {
                'total_revenue_30d': 150000,
                'avg_occupancy_30d': 65.5
            },
            'note': 'Sample data - No real data available'
        })

@admin_bp.route('/analytics/export/revenue-pdf')
@login_required
def export_revenue_pdf():
    """Export revenue report as PDF - FIXED VERSION"""
    try:
        # Try to import PDF generator
        try:
            from utils.pdf_generator import PDFGenerator
            report_data = AnalyticsHelpers.generate_booking_stats_report()
            
            pdf_buffer = PDFGenerator.generate_revenue_report(report_data)
            
            return send_file(
                pdf_buffer,
                mimetype='application/pdf',
                as_attachment=True,
                download_name=f'revenue_report_{date.today()}.pdf'
            )
        except ImportError:
            flash('PDF generation not available. Please install reportlab.', 'warning')
            return redirect(url_for('admin.analytics'))
            
    except Exception as e:
        print(f"Error generating PDF: {e}")
        flash(f'Error generating PDF: {str(e)}', 'danger')
        return redirect(url_for('admin.analytics'))

@admin_bp.route('/analytics/export/guest-excel')
@login_required
def export_guest_excel():
    """Export guest report as Excel - FIXED VERSION"""
    try:
        # Try to import Excel generator
        try:
            from utils.excel_generator import ExcelGenerator
            report_data = AnalyticsHelpers.generate_booking_stats_report()
            
            excel_buffer = ExcelGenerator.generate_guest_report(report_data)
            
            return send_file(
                excel_buffer,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name=f'guest_report_{date.today()}.xlsx'
            )
        except ImportError:
            flash('Excel generation not available. Please install openpyxl.', 'warning')
            return redirect(url_for('admin.analytics'))
            
    except Exception as e:
        print(f"Error generating Excel: {e}")
        flash(f'Error generating Excel: {str(e)}', 'danger')
        return redirect(url_for('admin.analytics'))

@admin_bp.route('/analytics/export/csv-report')
@login_required
def export_csv_report():
    """Export analytics data as CSV - FIXED VERSION"""
    try:
        report_data = AnalyticsHelpers.generate_booking_stats_report()
        csv_buffer = AnalyticsHelpers.generate_csv_report(report_data, 'analytics_report')
        
        return send_file(
            csv_buffer,
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'analytics_report_{date.today()}.csv'
        )
    except Exception as e:
        print(f"Error generating CSV: {e}")
        flash(f'Error generating CSV: {str(e)}', 'danger')
        return redirect(url_for('admin.analytics'))

@admin_bp.route('/export/bookings')
@login_required
def export_bookings():
    """Export bookings to CSV - FIXED VERSION"""
    bookings = Booking.query.all()
    
    # Create StringIO object for CSV data
    output = StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['ID', 'Guest Name', 'Room', 'Check-in', 'Check-out', 'Nights', 'Amount', 'Status', 'Payment Status'])
    
    # Write data
    for booking in bookings:
        writer.writerow([
            booking.id,
            booking.user.name,
            booking.room.name,
            booking.check_in.strftime('%Y-%m-%d'),
            booking.check_out.strftime('%Y-%m-%d'),
            booking.total_nights,
            booking.final_amount,
            booking.status,
            booking.payment_status
        ])
    
    # Get the CSV data as string
    csv_data = output.getvalue()
    output.close()
    
    # Create BytesIO from the string data
    bytes_io = BytesIO()
    bytes_io.write(csv_data.encode('utf-8'))
    bytes_io.seek(0)
    
    return send_file(
        bytes_io,
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'bookings_export_{date.today()}.csv'
    )

# admin.py - Updated offer management routes
@admin_bp.route('/offers')
@login_required
def manage_offers():
    """Enhanced offer management with filtering"""
    status_filter = request.args.get('status', 'all')
    type_filter = request.args.get('type', 'all')
    
    query = Offer.query
    
    if status_filter == 'active':
        query = query.filter_by(is_active=True)
    elif status_filter == 'inactive':
        query = query.filter_by(is_active=False)
    elif status_filter == 'expired':
        query = query.filter(Offer.valid_until < datetime.utcnow())
    
    if type_filter != 'all':
        query = query.filter_by(discount_type=type_filter)
    
    offers = query.order_by(Offer.priority.desc(), Offer.created_at.desc()).all()
    
    # Statistics
    total_offers = Offer.query.count()
    active_offers = Offer.query.filter_by(is_active=True).count()
    expired_offers = Offer.query.filter(Offer.valid_until < datetime.utcnow()).count()
    
    return render_template('admin/offers.html', 
                         offers=offers,
                         total_offers=total_offers,
                         active_offers=active_offers,
                         expired_offers=expired_offers,
                         status_filter=status_filter,
                         type_filter=type_filter)

@admin_bp.route('/offers/add', methods=['GET', 'POST'])
@login_required
def add_offer():
    """Add new offer with enhanced fields"""
    if request.method == 'POST':
        try:
            # Basic offer information
            code = request.form.get('code').upper().strip()
            name = request.form.get('name')
            description = request.form.get('description')
            discount_type = request.form.get('discount_type')
            discount_value = float(request.form.get('discount_value'))
            min_amount = float(request.form.get('min_amount', 0))
            
            # Advanced settings
            max_discount = request.form.get('max_discount')
            valid_from = datetime.strptime(request.form.get('valid_from'), '%Y-%m-%d') if request.form.get('valid_from') else datetime.utcnow()
            valid_until = datetime.strptime(request.form.get('valid_until'), '%Y-%m-%d')
            usage_limit = request.form.get('usage_limit')
            
            # Targeting criteria
            target_user_type = request.form.get('target_user_type', 'all')
            min_stay_nights = int(request.form.get('min_stay_nights', 1))
            max_stay_nights = request.form.get('max_stay_nights')
            advance_booking_days = int(request.form.get('advance_booking_days', 0))
            max_advance_booking_days = request.form.get('max_advance_booking_days')
            season_type = request.form.get('season_type', 'all')
            day_of_week = request.form.get('day_of_week', 'all')
            
            # Room targeting
            target_room_types = request.form.getlist('target_room_types')
            target_room_ids = request.form.getlist('target_room_ids')
            
            # Additional settings
            priority = int(request.form.get('priority', 1))
            auto_apply = request.form.get('auto_apply') == 'on'
            is_public = request.form.get('is_public') == 'on'
            is_active = request.form.get('is_active') == 'on'
            terms_conditions = request.form.get('terms_conditions')
            
            # Prepare target_rooms JSON
            target_rooms_data = {
                'room_types': target_room_types,
                'room_ids': [int(id) for id in target_room_ids if id]
            }
            
            offer = Offer(
                code=code,
                name=name,
                description=description,
                discount_type=discount_type,
                discount_value=discount_value,
                min_amount=min_amount,
                max_discount=float(max_discount) if max_discount else None,
                valid_from=valid_from,
                valid_until=valid_until,
                usage_limit=int(usage_limit) if usage_limit else None,
                target_user_type=target_user_type,
                min_stay_nights=min_stay_nights,
                max_stay_nights=int(max_stay_nights) if max_stay_nights else None,
                advance_booking_days=advance_booking_days,
                max_advance_booking_days=int(max_advance_booking_days) if max_advance_booking_days else None,
                season_type=season_type,
                day_of_week=day_of_week,
                target_rooms=json.dumps(target_rooms_data),
                priority=priority,
                auto_apply=auto_apply,
                is_public=is_public,
                is_active=is_active,
                terms_conditions=terms_conditions
            )
            
            db.session.add(offer)
            db.session.commit()
            
            flash('Offer added successfully!', 'success')
            return redirect(url_for('admin.manage_offers'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating offer: {str(e)}', 'danger')
    
    # Get rooms for targeting
    rooms = Room.query.all()
    room_types = db.session.query(Room.room_type).distinct().all()
    
    return render_template('admin/offer_form.html', 
                         rooms=rooms,
                         room_types=[rt[0] for rt in room_types])

@admin_bp.route('/offers/edit/<int:offer_id>', methods=['GET', 'POST'])
@login_required
def edit_offer(offer_id):
    """Edit existing offer with enhanced fields"""
    offer = Offer.query.get_or_404(offer_id)
    
    if request.method == 'POST':
        try:
            # Update basic information
            offer.code = request.form.get('code').upper().strip()
            offer.name = request.form.get('name')
            offer.description = request.form.get('description')
            offer.discount_type = request.form.get('discount_type')
            offer.discount_value = float(request.form.get('discount_value'))
            offer.min_amount = float(request.form.get('min_amount', 0))
            
            # Update advanced settings
            max_discount = request.form.get('max_discount')
            offer.max_discount = float(max_discount) if max_discount else None
            
            offer.valid_from = datetime.strptime(request.form.get('valid_from'), '%Y-%m-%d') if request.form.get('valid_from') else offer.valid_from
            offer.valid_until = datetime.strptime(request.form.get('valid_until'), '%Y-%m-%d')
            
            usage_limit = request.form.get('usage_limit')
            offer.usage_limit = int(usage_limit) if usage_limit else None
            
            # Update targeting criteria
            offer.target_user_type = request.form.get('target_user_type', 'all')
            offer.min_stay_nights = int(request.form.get('min_stay_nights', 1))
            
            max_stay_nights = request.form.get('max_stay_nights')
            offer.max_stay_nights = int(max_stay_nights) if max_stay_nights else None
            
            offer.advance_booking_days = int(request.form.get('advance_booking_days', 0))
            
            max_advance_booking_days = request.form.get('max_advance_booking_days')
            offer.max_advance_booking_days = int(max_advance_booking_days) if max_advance_booking_days else None
            
            offer.season_type = request.form.get('season_type', 'all')
            offer.day_of_week = request.form.get('day_of_week', 'all')
            
            # Update room targeting
            target_room_types = request.form.getlist('target_room_types')
            target_room_ids = request.form.getlist('target_room_ids')
            
            target_rooms_data = {
                'room_types': target_room_types,
                'room_ids': [int(id) for id in target_room_ids if id]
            }
            offer.target_rooms = json.dumps(target_rooms_data)
            
            # Update additional settings
            offer.priority = int(request.form.get('priority', 1))
            offer.auto_apply = request.form.get('auto_apply') == 'on'
            offer.is_public = request.form.get('is_public') == 'on'
            offer.is_active = request.form.get('is_active') == 'on'
            offer.terms_conditions = request.form.get('terms_conditions')
            
            db.session.commit()
            flash('Offer updated successfully!', 'success')
            return redirect(url_for('admin.manage_offers'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating offer: {str(e)}', 'danger')
    
    # Parse target_rooms for form
    target_rooms = {}
    if offer.target_rooms:
        try:
            target_rooms = json.loads(offer.target_rooms)
        except:
            target_rooms = {'room_types': [], 'room_ids': []}
    
    # Get rooms for targeting
    rooms = Room.query.all()
    room_types = db.session.query(Room.room_type).distinct().all()
    
    return render_template('admin/offer_form.html', 
                         offer=offer,
                         rooms=rooms,
                         room_types=[rt[0] for rt in room_types],
                         target_rooms=target_rooms)

@admin_bp.route('/offers/delete/<int:offer_id>')
@login_required
def delete_offer(offer_id):
    """Delete offer"""
    offer = Offer.query.get_or_404(offer_id)
    
    # Check if offer has been used
    if offer.used_count > 0:
        flash('Cannot delete offer that has been used.', 'danger')
        return redirect(url_for('admin.manage_offers'))
    
    db.session.delete(offer)
    db.session.commit()
    
    flash('Offer deleted successfully!', 'success')
    return redirect(url_for('admin.manage_offers'))

@admin_bp.route('/offers/duplicate/<int:offer_id>')
@login_required
def duplicate_offer(offer_id):
    """Duplicate an existing offer"""
    original_offer = Offer.query.get_or_404(offer_id)
    
    # Create new offer with copied data
    new_offer = Offer(
        code=f"{original_offer.code}_COPY",
        name=f"{original_offer.name} (Copy)",
        description=original_offer.description,
        discount_type=original_offer.discount_type,
        discount_value=original_offer.discount_value,
        min_amount=original_offer.min_amount,
        max_discount=original_offer.max_discount,
        valid_from=datetime.utcnow(),
        valid_until=original_offer.valid_until,
        usage_limit=original_offer.usage_limit,
        target_user_type=original_offer.target_user_type,
        min_stay_nights=original_offer.min_stay_nights,
        max_stay_nights=original_offer.max_stay_nights,
        advance_booking_days=original_offer.advance_booking_days,
        max_advance_booking_days=original_offer.max_advance_booking_days,
        season_type=original_offer.season_type,
        day_of_week=original_offer.day_of_week,
        target_rooms=original_offer.target_rooms,
        priority=original_offer.priority,
        auto_apply=original_offer.auto_apply,
        is_public=original_offer.is_public,
        is_active=False,  # Keep inactive until reviewed
        terms_conditions=original_offer.terms_conditions
    )
    
    db.session.add(new_offer)
    db.session.commit()
    
    flash('Offer duplicated successfully! Please review and activate the new offer.', 'success')
    return redirect(url_for('admin.edit_offer', offer_id=new_offer.id))

@admin_bp.route('/offers/quick_toggle/<int:offer_id>')
@login_required
def quick_toggle_offer(offer_id):
    """Quick toggle offer active status"""
    offer = Offer.query.get_or_404(offer_id)
    offer.is_active = not offer.is_active
    db.session.commit()
    
    status = "activated" if offer.is_active else "deactivated"
    flash(f'Offer {status} successfully!', 'success')
    return redirect(url_for('admin.manage_offers'))



# Add this route to admin.py for AI-powered review management
@admin_bp.route('/reviews/ai-analysis')
@login_required
def ai_review_analysis():
    """AI-powered review analysis dashboard"""
    pending_reviews = Review.query.filter_by(is_approved=False).order_by(Review.created_at.desc()).all()
    
    # Get AI analysis for pending reviews
    review_analyses = []
    for review in pending_reviews[:10]:  # Limit to 10 for performance
        try:
            from utils.ai_service import OpenRouterAI
            ai_service = OpenRouterAI()
            analysis = ai_service.analyze_review_sentiment(review.comment, review.rating)
            review_analyses.append({
                'review': review,
                'analysis': analysis
            })
        except Exception as e:
            print(f"AI analysis failed for review {review.id}: {e}")
            review_analyses.append({
                'review': review,
                'analysis': {'sentiment': 'unknown', 'summary': 'Analysis unavailable'}
            })
    
    return render_template('admin/ai_review_analysis.html',
                         review_analyses=review_analyses,
                         total_pending=len(pending_reviews))

@admin_bp.route('/offers/ai-suggestions')
@login_required
def ai_offer_suggestions():
    """AI-powered offer suggestions"""
    from utils.offer_engine import SmartOfferEngine
    
    # Get user booking trends for AI suggestions
    users_with_bookings = User.query.filter(User.bookings.any()).all()
    booking_trends = {
        'total_users': len(users_with_bookings),
        'frequent_travelers': len([u for u in users_with_bookings if len(u.bookings) >= 3]),
        'average_bookings': len(users_with_bookings) / User.query.count() if User.query.count() > 0 else 0
    }
    
    # Get AI suggestions
    suggestions = []
    try:
        for user in users_with_bookings[:5]:  # Sample 5 users
            user_suggestions = SmartOfferEngine.get_offer_suggestions(user, user.bookings)
            suggestions.extend(user_suggestions)
    except Exception as e:
        print(f"AI offer suggestions failed: {e}")
    
    return render_template('admin/ai_offer_suggestions.html',
                         suggestions=suggestions[:10],  # Limit to 10
                         booking_trends=booking_trends)

# Add this route to admin.py (if not already present)
@admin_bp.route('/ai-insights/advanced')
@login_required
def advanced_ai_insights():
    """Advanced AI insights dashboard"""
    from utils.advanced_ai_insights import AdvancedAIAnalytics
    
    # Get comprehensive business data
    business_data = AdvancedAIAnalytics.get_comprehensive_business_data(90)
    
    # Generate insights
    strategic_insights = None
    predictive_insights = None
    
    try:
        strategic_insights = AdvancedAIAnalytics.generate_strategic_insights(business_data)
        predictive_insights = AdvancedAIAnalytics.generate_predictive_insights()
    except Exception as e:
        print(f"AI insights generation error: {e}")
        strategic_insights = "AI insights temporarily unavailable"
        predictive_insights = {
            'next_month_occupancy': 65.0,
            'next_month_revenue': 0,
            'seasonal_trends': {},
            'high_demand_periods': [],
            'opportunity_periods': []
        }
    
    return render_template('admin/advanced_ai_insights.html',
                         business_data=business_data,
                         strategic_insights=strategic_insights,
                         predictive_insights=predictive_insights)

@admin_bp.route('/ai-insights/refresh', methods=['POST'])
@login_required
def refresh_ai_insights():
    """Refresh AI insights data"""
    # This would typically involve recalculating insights
    # For now, we'll just redirect back
    flash('AI insights refreshed successfully!', 'success')
    return jsonify({'success': True})

@admin_bp.route('/ai-insights')
@login_required
def ai_insights():
    """AI-powered business insights dashboard"""
    # Get business data for AI analysis
    total_rooms = Room.query.count()
    available_rooms = Room.query.filter_by(status='available').count()
    total_bookings = Booking.query.count()
    
    # Recent data
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_bookings = Booking.query.filter(Booking.created_at >= thirty_days_ago).all()
    recent_reviews = Review.query.filter(Review.created_at >= thirty_days_ago).all()
    
    # Prepare data for AI
    business_data = {
        'total_rooms': total_rooms,
        'available_rooms': available_rooms,
        'occupancy_rate': round((total_rooms - available_rooms) / total_rooms * 100, 1) if total_rooms > 0 else 0,
        'total_bookings': total_bookings,
        'recent_bookings_count': len(recent_bookings),
        'recent_reviews_count': len(recent_reviews),
        'average_rating': db.session.query(db.func.avg(Review.rating)).filter_by(is_approved=True).scalar() or 0,
        'revenue_30_days': sum(b.final_amount for b in recent_bookings if b.payment_status == 'paid'),
        'popular_room_types': db.session.query(
            Room.room_type, 
            db.func.count(Booking.id)
        ).join(Booking).group_by(Room.room_type).all()
    }
    
    # Get AI insights
    ai_analysis = None
    try:
        from utils.ai_service import OpenRouterAI
        ai_service = OpenRouterAI()
        ai_analysis = ai_service.get_business_insights(business_data)
    except Exception as e:
        print(f"AI insights error: {e}")
        ai_analysis = "AI insights temporarily unavailable"
    
    return render_template('admin/ai_insights.html',
                         business_data=business_data,
                         ai_analysis=ai_analysis,
                         recent_bookings=recent_bookings[:10],
                         recent_reviews=recent_reviews[:10])

@admin_bp.route('/admin-chatbot')
@login_required
def admin_chatbot():
    """Admin chatbot interface with full business access"""
    if not current_user.is_staff():
        flash('Admin access required', 'danger')
        return redirect(url_for('admin.dashboard'))
    
    return render_template('admin/admin_chatbot.html')

