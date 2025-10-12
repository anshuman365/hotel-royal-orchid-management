from app import db
from datetime import datetime

class Room(db.Model):
    __tablename__ = 'rooms'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    room_type = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    size = db.Column(db.String(20))
    amenities = db.Column(db.Text)
    description = db.Column(db.Text)
    images = db.Column(db.Text)
    status = db.Column(db.String(20), default='available')
    max_adults = db.Column(db.Integer, default=2)
    max_children = db.Column(db.Integer, default=2)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships - use back_populates consistently
    bookings = db.relationship('Booking', back_populates='room', lazy=True)
    reviews = db.relationship('Review', back_populates='room', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'type': self.room_type,
            'price': float(self.price),
            'capacity': self.capacity,
            'size': self.size,
            'amenities': self.amenities,
            'description': self.description,
            'images': self.images,
            'status': self.status,
            'max_adults': self.max_adults,
            'max_children': self.max_children
        }

    def get_average_rating(self):
        """Calculate average rating from approved reviews"""
        approved_reviews = [r for r in self.reviews if r.is_approved]
        if not approved_reviews:
            return 0
        return sum(review.rating for review in approved_reviews) / len(approved_reviews)
    
    def get_rating_count(self, rating):
        """Get count of reviews with specific rating"""
        return len([r for r in self.reviews if r.is_approved and r.rating == rating])
    
    def get_approved_reviews(self):
        """Get all approved reviews"""
        return [r for r in self.reviews if r.is_approved]
    
    def user_can_review(self, user_id):
        """Check if user can review this room"""
        from models.booking import Booking
        from datetime import date
        eligible_booking = Booking.query.filter(
            Booking.user_id == user_id,
            Booking.room_id == self.id,
            Booking.status.in_(['checked_in', 'checked_out', 'completed']),
            Booking.check_in <= date.today()
        ).first()
        print("date.today()", date.today())
        print("Time in database", Booking.query.filter(Booking.check_in))
        print("user_id", user_id)
        print("eligible_booking", eligible_booking)
        
        bookings = Booking.query.filter_by(user_id=user_id, room_id=self.id).all()
        print("User bookings for this room:", [(b.id, b.status, b.check_in) for b in bookings])
        
        if not eligible_booking:
            return False
        # Check if user already reviewed this booking
        from models.review import Review
        existing_review = Review.query.filter_by(
            booking_id=eligible_booking.id,
            user_id=user_id
        ).first()
        return not existing_review
    
    def is_available(self, check_in, check_out):
        """Check if room is available for given dates"""
        from models.booking import Booking
        conflicting_booking = Booking.query.filter(
            Booking.room_id == self.id,
            Booking.status.in_(['confirmed', 'pending']),
            Booking.check_in < check_out,
            Booking.check_out > check_in
        ).first()
        return conflicting_booking is None

    def get_detailed_ratings(self):
        """Get average detailed ratings from approved reviews"""
        approved_reviews = [r for r in self.reviews if r.is_approved]
        if not approved_reviews:
            return {
                'cleanliness': 0,
                'comfort': 0,
                'location': 0,
                'amenities': 0,
                'service': 0
            }

        return {
            'cleanliness': sum(r.cleanliness_rating for r in approved_reviews) / len(approved_reviews),
            'comfort': sum(r.comfort_rating for r in approved_reviews) / len(approved_reviews),
            'location': sum(r.location_rating for r in approved_reviews) / len(approved_reviews),
            'amenities': sum(r.amenities_rating for r in approved_reviews) / len(approved_reviews),
            'service': sum(r.service_rating for r in approved_reviews) / len(approved_reviews)
        }

    def get_review_stats(self):
        """Get comprehensive review statistics"""
        approved_reviews = [r for r in self.reviews if r.is_approved]
        total_reviews = len(approved_reviews)

        if not approved_reviews:
            return {
                'average_rating': 0,
                'total_reviews': 0,
                'rating_breakdown': {1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
                'recommendation_rate': 0
            }

        average_rating = sum(review.rating for review in approved_reviews) / total_reviews

        # Rating breakdown
        rating_breakdown = {i: 0 for i in range(1, 6)}
        for review in approved_reviews:
            rating_breakdown[review.rating] += 1

        # Recommendation rate (percentage of 4-5 star reviews)
        positive_reviews = len([r for r in approved_reviews if r.rating >= 4])
        recommendation_rate = (positive_reviews / total_reviews) * 100

        return {
            'average_rating': round(average_rating, 1),
            'total_reviews': total_reviews,
            'rating_breakdown': rating_breakdown,
            'recommendation_rate': round(recommendation_rate, 1)
        }

    def __repr__(self):
        return f'<Room {self.name} - {self.room_type}>'