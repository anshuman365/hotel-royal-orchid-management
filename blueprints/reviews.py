from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, session
from flask_login import login_required, current_user
from app import db
from models.review import Review, review_helpful_votes
from models.booking import Booking
from models.room import Room
from datetime import datetime, date
import json
from utils.ai_service import OpenRouterAI  # NEW IMPORT

reviews_bp = Blueprint('reviews', __name__)

@reviews_bp.route('/room/<int:room_id>/review', methods=['GET', 'POST'])
@login_required
def add_review(room_id):
    """Add review for a room with enhanced rating system"""
    room = Room.query.get_or_404(room_id)
    
    # Check if user has eligible booking for this room
    eligible_booking = Booking.query.filter(
        Booking.user_id == current_user.id,
        Booking.room_id == room_id,
        Booking.status.in_(['checked_out', 'completed', 'checked_in']),
        Booking.check_in <= date.today()
    ).first()
    
    if not eligible_booking:
        flash('You can only review rooms you have stayed in after check-in.', 'danger')
        return redirect(url_for('main.room_detail', room_id=room_id))
    
    # Check if user already reviewed this booking
    existing_review = Review.query.filter_by(
        booking_id=eligible_booking.id,
        user_id=current_user.id
    ).first()
    
    if existing_review:
        flash('You have already reviewed this booking.', 'info')
        return redirect(url_for('main.room_detail', room_id=room_id))
    
    if request.method == 'POST':
        rating = request.form.get('rating', type=int)
        title = request.form.get('title')
        comment = request.form.get('comment')
        
        # Detailed ratings
        cleanliness_rating = request.form.get('cleanliness_rating', type=int, default=5)
        comfort_rating = request.form.get('comfort_rating', type=int, default=5)
        location_rating = request.form.get('location_rating', type=int, default=5)
        amenities_rating = request.form.get('amenities_rating', type=int, default=5)
        service_rating = request.form.get('service_rating', type=int, default=5)
        
        if not rating or rating < 1 or rating > 5:
            flash('Please provide a valid rating between 1 and 5.', 'danger')
            return render_template('add_review.html', room=room, booking=eligible_booking)
        
        # Validate detailed ratings
        detailed_ratings = [cleanliness_rating, comfort_rating, location_rating, amenities_rating, service_rating]
        if any(r < 1 or r > 5 for r in detailed_ratings):
            flash('All detailed ratings must be between 1 and 5.', 'danger')
            return render_template('add_review.html', room=room, booking=eligible_booking)
        
        review = Review(
            user_id=current_user.id,
            room_id=room_id,
            booking_id=eligible_booking.id,
            rating=rating,
            title=title,
            comment=comment,
            cleanliness_rating=cleanliness_rating,
            comfort_rating=comfort_rating,
            location_rating=location_rating,
            amenities_rating=amenities_rating,
            service_rating=service_rating,
            is_approved=False,
            is_verified=True  # Mark as verified since they actually stayed
        )
        
        db.session.add(review)
        db.session.commit()
        
        # NEW: AI Analysis for admin
        try:
            ai_service = OpenRouterAI()
            ai_analysis = ai_service.analyze_review_sentiment(comment, rating)
            
            # Store AI analysis in session for admin to see
            review_analysis = session.get('pending_review_analysis', {})
            review_analysis[str(review.id)] = {
                'analysis': ai_analysis,
                'timestamp': datetime.now().isoformat()
            }
            session['pending_review_analysis'] = review_analysis
            
        except Exception as e:
            print(f"AI analysis failed: {e}")
            # Continue without AI analysis
        
        # Update room average rating and detailed ratings
        update_room_ratings(room_id)
        
        flash('Thank you for your review! It will be visible after approval.', 'success')
        return redirect(url_for('main.room_detail', room_id=room_id))
    
    return render_template('add_review.html', room=room, booking=eligible_booking)

@reviews_bp.route('/review/<int:review_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_review(review_id):
    """Edit existing review"""
    review = Review.query.get_or_404(review_id)
    
    if review.user_id != current_user.id and not current_user.is_staff():
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        review.rating = request.form.get('rating', type=int)
        review.title = request.form.get('title')
        review.comment = request.form.get('comment')
        
        # Update detailed ratings
        review.cleanliness_rating = request.form.get('cleanliness_rating', type=int, default=5)
        review.comfort_rating = request.form.get('comfort_rating', type=int, default=5)
        review.location_rating = request.form.get('location_rating', type=int, default=5)
        review.amenities_rating = request.form.get('amenities_rating', type=int, default=5)
        review.service_rating = request.form.get('service_rating', type=int, default=5)
        
        review.is_approved = False  # Require re-approval after edit
        review.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        # Update room average ratings
        update_room_ratings(review.room_id)
        
        flash('Review updated successfully! It will be visible after approval.', 'success')
        return redirect(url_for('main.room_detail', room_id=review.room_id))
    
    return render_template('edit_review.html', review=review)

@reviews_bp.route('/review/<int:review_id>/delete')
@login_required
def delete_review(review_id):
    """Delete review"""
    review = Review.query.get_or_404(review_id)
    room_id = review.room_id
    
    if review.user_id != current_user.id and not current_user.is_staff():
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))
    
    db.session.delete(review)
    db.session.commit()
    
    # Update room average ratings
    update_room_ratings(room_id)
    
    flash('Review deleted successfully.', 'success')
    return redirect(url_for('main.room_detail', room_id=room_id))

@reviews_bp.route('/review/<int:review_id>/helpful', methods=['POST'])
@login_required
def mark_helpful(review_id):
    """Mark review as helpful"""
    review = Review.query.get_or_404(review_id)
    
    if review.mark_helpful(current_user.id):
        db.session.commit()
        return jsonify({
            'success': True,
            'helpful_count': review.helpful_count,
            'message': 'Thank you for your feedback!'
        })
    else:
        return jsonify({
            'success': False,
            'message': 'You have already marked this review as helpful.'
        })

@reviews_bp.route('/review/<int:review_id>/reply', methods=['POST'])
@login_required
def add_reply(review_id):
    """Add management reply to review"""
    if not current_user.is_staff():
        return jsonify({'success': False, 'message': 'Access denied.'}), 403
    
    review = Review.query.get_or_404(review_id)
    reply_text = request.json.get('reply')
    
    if not reply_text:
        return jsonify({'success': False, 'message': 'Reply text is required.'}), 400
    
    review.reply = reply_text
    review.reply_date = datetime.utcnow()
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Reply added successfully.',
        'reply': review.reply,
        'reply_date': review.reply_date.strftime('%B %d, %Y')
    })

# NEW AI-ENHANCED ROUTES
@reviews_bp.route('/review/<int:review_id>/ai-analysis')
@login_required
def get_ai_analysis(review_id):
    """Get AI analysis of a review (Admin only)"""
    if not current_user.is_staff():
        return jsonify({'success': False, 'message': 'Access denied.'}), 403
    
    review = Review.query.get_or_404(review_id)
    
    try:
        ai_service = OpenRouterAI()
        analysis = ai_service.analyze_review_sentiment(review.comment, review.rating)
        
        return jsonify({
            'success': True,
            'analysis': analysis,
            'review_id': review_id
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'AI analysis failed: {str(e)}'
        })

@reviews_bp.route('/review/<int:review_id>/ai-response', methods=['POST'])
@login_required
def generate_ai_response(review_id):
    """Generate AI-powered management response"""
    if not current_user.is_staff():
        return jsonify({'success': False, 'message': 'Access denied.'}), 403
    
    review = Review.query.get_or_404(review_id)
    
    try:
        # Get or create analysis
        analysis_data = request.json.get('analysis')
        if not analysis_data:
            ai_service = OpenRouterAI()
            analysis_data = ai_service.analyze_review_sentiment(review.comment, review.rating)
        
        # Generate response
        ai_service = OpenRouterAI()
        response = ai_service.generate_management_response(review, analysis_data)
        
        return jsonify({
            'success': True,
            'response': response,
            'review_id': review_id
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'AI response generation failed: {str(e)}'
        })

def update_room_ratings(room_id):
    """Update room's average rating and detailed ratings"""
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
        
        # Store these in the room model (you might want to add these fields)
        # For now, we'll calculate them on the fly in templates
        
    return

# Enhanced API endpoints
@reviews_bp.route('/api/room/<int:room_id>/reviews')
def get_room_reviews(room_id):
    """Get room reviews API with filtering and sorting"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 5, type=int)
    sort_by = request.args.get('sort_by', 'newest')  # newest, highest, lowest, most_helpful
    rating_filter = request.args.get('rating', type=int)
    
    query = Review.query.filter_by(
        room_id=room_id, 
        is_approved=True
    )
    
    # Filter by rating if specified
    if rating_filter and 1 <= rating_filter <= 5:
        query = query.filter(Review.rating == rating_filter)
    
    # Apply sorting
    if sort_by == 'highest':
        query = query.order_by(Review.rating.desc(), Review.created_at.desc())
    elif sort_by == 'lowest':
        query = query.order_by(Review.rating.asc(), Review.created_at.desc())
    elif sort_by == 'most_helpful':
        query = query.order_by(Review.helpful_count.desc(), Review.created_at.desc())
    else:  # newest
        query = query.order_by(Review.created_at.desc())
    
    reviews = query.paginate(
        page=page, 
        per_page=per_page, 
        error_out=False
    )
    
    return jsonify({
        'reviews': [review.to_dict() for review in reviews.items],
        'has_next': reviews.has_next,
        'next_page': reviews.next_num,
        'total': reviews.total,
        'pages': reviews.pages
    })

@reviews_bp.route('/api/room/<int:room_id>/review-stats')
def get_review_stats(room_id):
    """Get detailed review statistics for a room"""
    approved_reviews = Review.query.filter_by(
        room_id=room_id, 
        is_approved=True
    ).all()
    
    if not approved_reviews:
        return jsonify({
            'average_rating': 0,
            'total_reviews': 0,
            'rating_breakdown': {1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
            'detailed_ratings': {
                'cleanliness': 0,
                'comfort': 0,
                'location': 0,
                'amenities': 0,
                'service': 0
            }
        })
    
    total_reviews = len(approved_reviews)
    average_rating = sum(review.rating for review in approved_reviews) / total_reviews
    
    # Rating breakdown
    rating_breakdown = {i: 0 for i in range(1, 6)}
    for review in approved_reviews:
        rating_breakdown[review.rating] += 1
    
    # Detailed ratings averages
    detailed_ratings = {
        'cleanliness': sum(review.cleanliness_rating for review in approved_reviews) / total_reviews,
        'comfort': sum(review.comfort_rating for review in approved_reviews) / total_reviews,
        'location': sum(review.location_rating for review in approved_reviews) / total_reviews,
        'amenities': sum(review.amenities_rating for review in approved_reviews) / total_reviews,
        'service': sum(review.service_rating for review in approved_reviews) / total_reviews
    }
    
    return jsonify({
        'average_rating': round(average_rating, 1),
        'total_reviews': total_reviews,
        'rating_breakdown': rating_breakdown,
        'detailed_ratings': detailed_ratings
    })