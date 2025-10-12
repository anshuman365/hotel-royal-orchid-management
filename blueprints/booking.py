from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, current_app
from flask_login import login_required, current_user
from app import db
from models.room import Room
from models.booking import Booking
from models.payment import Payment
from models.offer import Offer
from datetime import datetime, date, timedelta
import json
from utils.payment_gateway import create_razorpay_order, verify_payment_signature
from utils.email_service import send_booking_confirmation, send_welcome_email
from utils.sms_service import send_booking_sms
from utils.offer_engine import SmartOfferEngine

booking_bp = Blueprint('booking', __name__)

@booking_bp.route('/book/<int:room_id>', methods=['GET', 'POST'])
@login_required
def book_room(room_id):
    """Booking form with improved date handling"""
    room = Room.query.get_or_404(room_id)
    
    # Get dates from query parameters or form with better defaults
    check_in_str = request.args.get('check_in') or request.form.get('check_in')
    check_out_str = request.args.get('check_out') or request.form.get('check_out')
    adults = request.args.get('guests', 1, type=int) or request.form.get('adults', 1, type=int)
    children = request.args.get('children', 0, type=int) or request.form.get('children', 0, type=int)
    
    # If no dates provided, set default dates (tomorrow and day after tomorrow)
    if not check_in_str or not check_out_str:
        tomorrow = date.today() + timedelta(days=1)
        day_after = tomorrow + timedelta(days=1)
        check_in_str = tomorrow.strftime('%Y-%m-%d')
        check_out_str = day_after.strftime('%Y-%m-%d')
        flash('Please confirm your dates for booking', 'info')
    
    try:
        check_in = datetime.strptime(check_in_str, '%Y-%m-%d').date()
        check_out = datetime.strptime(check_out_str, '%Y-%m-%d').date()
    except ValueError:
        flash('Invalid date format. Please select valid dates.', 'danger')
        return redirect(url_for('main.room_detail', room_id=room_id))
    
    # Validate dates
    today = date.today()
    if check_in < today:
        flash('Check-in date cannot be in the past.', 'danger')
        return redirect(url_for('main.room_detail', room_id=room_id))
    
    if check_out <= check_in:
        flash('Check-out date must be after check-in date.', 'danger')
        return redirect(url_for('main.room_detail', room_id=room_id))
    
    # Check availability
    if not room.is_available(check_in, check_out):
        flash('Sorry, this room is not available for the selected dates.', 'danger')
        return redirect(url_for('main.room_detail', room_id=room_id))
    
    # Calculate pricing
    nights = (check_out - check_in).days
    base_amount = room.price * nights
    tax_amount = base_amount * 0.18
    total_amount = base_amount + tax_amount
    
    # Get auto-apply offers
    booking_data = {
        'check_in': check_in,
        'check_out': check_out,
        'room_type': room.room_type,
        'total_amount': total_amount
    }
    
    auto_apply_offers = Offer.get_auto_apply_offers(current_user, booking_data, room)
    applied_offers = []
    discount_amount = 0
    
    # Apply auto-apply offers
    for offer in auto_apply_offers:
        offer_discount = offer.calculate_discount(total_amount, nights)
        discount_amount += offer_discount
        applied_offers.append({
            'offer': offer,
            'discount': offer_discount
        })
    
    final_amount = max(total_amount - discount_amount, 0)
    
    if request.method == 'POST':
        # Handle manual coupon code
        coupon_code = request.form.get('coupon_code')
        manual_discount = 0
        
        if coupon_code:
            offer = Offer.query.filter_by(code=coupon_code).first()
            if offer and offer.is_valid(current_user, booking_data, room):
                manual_discount = offer.calculate_discount(total_amount, nights)
                final_amount = total_amount - discount_amount - manual_discount
                applied_offers.append({
                    'offer': offer,
                    'discount': manual_discount,
                    'manual': True
                })
                flash(f'Coupon applied! Discount: ₹{manual_discount:.2f}', 'success')
            else:
                flash('Invalid or expired coupon code.', 'danger')
        
        # Create booking
        booking = Booking(
            user_id=current_user.id,
            room_id=room_id,
            check_in=check_in,
            check_out=check_out,
            adults=adults,
            children=children,
            total_nights=nights,
            base_amount=base_amount,
            tax_amount=tax_amount,
            discount_amount=discount_amount + manual_discount,
            total_amount=total_amount,
            final_amount=final_amount,
            coupon_code=coupon_code,
            special_requests=request.form.get('special_requests', ''),
            status='pending',
            payment_status='pending'
        )
        
        db.session.add(booking)
        db.session.commit()
        
        # Record offer usage
        for applied_offer in applied_offers:
            applied_offer['offer'].increment_usage()
        
        # Create Razorpay order
        razorpay_order = create_razorpay_order(
            amount=final_amount,
            receipt=f'booking_{booking.id}'
        )
        
        if razorpay_order:
            # Store Razorpay order ID in booking
            booking.razorpay_order_id = razorpay_order['id']
            db.session.commit()
            
            # Redirect to payment page
            return redirect(url_for('booking.process_payment', booking_id=booking.id))
        else:
            flash('Payment gateway error. Please try again.', 'danger')
            return redirect(url_for('main.room_detail', room_id=room_id))

    # Get personalized offers
    booking_data = {
        'check_in': check_in,
        'check_out': check_out,
        'room_type': room.room_type,
        'total_amount': total_amount
    }
    personalized_offers = SmartOfferEngine.generate_personalized_offers(current_user, booking_data)
    
    return render_template('booking.html',
                         room=room,
                         check_in=check_in_str,
                         check_out=check_out_str,
                         adults=adults,
                         children=children,
                         nights=nights,
                         base_amount=base_amount,
                         tax_amount=tax_amount,
                         total_amount=total_amount,
                         discount_amount=discount_amount,
                         final_amount=final_amount,
                         auto_apply_offers=auto_apply_offers,
                         personalized_offers=personalized_offers,
                         applied_offers=applied_offers)

@booking_bp.route('/payment/<int:booking_id>', methods=['GET', 'POST'])
@login_required
def process_payment(booking_id):
    """Process payment for booking"""
    booking = Booking.query.get_or_404(booking_id)
    
    # Ensure user owns this booking
    if booking.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))
    
    if booking.payment_status == 'paid':
        flash('Payment already completed for this booking.', 'info')
        return redirect(url_for('booking.booking_confirm', booking_id=booking.id))
    
    # Create Razorpay order if not exists
    if not booking.razorpay_order_id:
        razorpay_order = create_razorpay_order(
            amount=booking.final_amount,
            receipt=f'booking_{booking.id}'
        )
        if razorpay_order:
            booking.razorpay_order_id = razorpay_order['id']
            db.session.commit()
        else:
            flash('Payment gateway error. Please try again.', 'danger')
            return redirect(url_for('booking.book_room', room_id=booking.room_id))
    
    if request.method == 'POST':
        # Handle payment verification
        razorpay_payment_id = request.form.get('razorpay_payment_id')
        razorpay_order_id = request.form.get('razorpay_order_id')
        razorpay_signature = request.form.get('razorpay_signature')
        
        # Debug information
        print(f"Payment ID: {razorpay_payment_id}")
        print(f"Order ID: {razorpay_order_id}")
        print(f"Signature: {razorpay_signature}")
        
        if razorpay_payment_id and razorpay_order_id and razorpay_signature:
            if verify_payment_signature(razorpay_order_id, razorpay_payment_id, razorpay_signature):
                # Payment successful
                booking.payment_status = 'paid'
                booking.status = 'confirmed'
                
                # Create payment record
                payment = Payment(
                    booking_id=booking.id,
                    amount=booking.final_amount,
                    payment_method='razorpay',
                    payment_id=razorpay_payment_id,
                    payment_status='completed',
                    razorpay_order_id=razorpay_order_id,
                    razorpay_payment_id=razorpay_payment_id,
                    razorpay_signature=razorpay_signature
                )
                
                db.session.add(payment)
                db.session.commit()
                
                # Send confirmation email and SMS
                try:
                    send_booking_confirmation(booking, current_user.email)
                    if current_user.phone:
                        send_booking_sms(booking, current_user.phone)
                except Exception as e:
                    print(f"Notification sending failed: {e}")
                    # Don't fail the booking if notifications fail
                
                flash('Payment successful! Your booking is confirmed.', 'success')
                return redirect(url_for('booking.booking_confirm', booking_id=booking.id))
            else:
                flash('Payment verification failed. Please try again.', 'danger')
        else:
            flash('Payment details missing. Please try again.', 'danger')
    
    return render_template('payment.html', 
                         booking=booking,
                         razorpay_key=current_app.config['RAZORPAY_KEY_ID'])

@booking_bp.route('/booking/confirm/<int:booking_id>')
@login_required
def booking_confirm(booking_id):
    """Booking confirmation page"""
    booking = Booking.query.get_or_404(booking_id)
    
    # Ensure user owns this booking or is admin
    if booking.user_id != current_user.id and not current_user.is_staff():
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))
    
    return render_template('booking-confirm.html', booking=booking)

@booking_bp.route('/booking/cancel/<int:booking_id>')
@login_required
def cancel_booking(booking_id):
    """Cancel booking"""
    booking = Booking.query.get_or_404(booking_id)
    
    # Ensure user owns this booking or is admin
    if booking.user_id != current_user.id and not current_user.is_staff():
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))
    
    if booking.status in ['pending', 'confirmed']:
        booking.status = 'cancelled'
        db.session.commit()
        
        # Send cancellation email
        try:
            from utils.email_service import send_booking_cancellation
            send_booking_cancellation(booking, current_user.email)
        except Exception as e:
            print(f"Cancellation email failed: {e}")
        
        flash('Booking cancelled successfully.', 'success')
    else:
        flash('Cannot cancel this booking.', 'danger')
    
    return redirect(url_for('auth.profile'))

@booking_bp.route('/get_offers', methods=['POST'])
@login_required
def get_offers():
    """Get personalized offers based on booking details"""
    data = request.get_json()
    
    booking_data = {
        'check_in': datetime.strptime(data.get('check_in'), '%Y-%m-%d').date() if data.get('check_in') else None,
        'check_out': datetime.strptime(data.get('check_out'), '%Y-%m-%d').date() if data.get('check_out') else None,
        'room_type': data.get('room_type'),
        'total_amount': float(data.get('total_amount', 0))
    }
    
    offers = SmartOfferEngine.generate_personalized_offers(current_user, booking_data)
    
    return jsonify({
        'success': True,
        'offers': [offer.to_dict() for offer in offers]
    })

@booking_bp.route('/apply_coupon', methods=['POST'])
@login_required
def apply_coupon():
    """Apply coupon code and calculate discount"""
    data = request.get_json()
    coupon_code = data.get('coupon_code')
    total_amount = float(data.get('total_amount', 0))
    
    offer = Offer.query.filter_by(code=coupon_code).first()
    
    if offer and offer.is_valid():
        discount = offer.calculate_discount(total_amount)
        final_amount = total_amount - discount
        
        return jsonify({
            'success': True,
            'discount': discount,
            'final_amount': final_amount,
            'message': f'Coupon applied! Discount: ₹{discount:.2f}'
        })
    else:
        return jsonify({
            'success': False,
            'message': 'Invalid or expired coupon code.'
        })