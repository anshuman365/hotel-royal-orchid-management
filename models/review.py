from app import db
from datetime import datetime
from sqlalchemy import CheckConstraint

class Review(db.Model):
    __tablename__ = 'reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=False)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(200))
    comment = db.Column(db.Text)
    
    # New fields for enhanced review system
    cleanliness_rating = db.Column(db.Integer, default=5)
    comfort_rating = db.Column(db.Integer, default=5)
    location_rating = db.Column(db.Integer, default=5)
    amenities_rating = db.Column(db.Integer, default=5)
    service_rating = db.Column(db.Integer, default=5)
    
    is_approved = db.Column(db.Boolean, default=False)
    is_verified = db.Column(db.Boolean, default=False)  # Verified stay
    helpful_count = db.Column(db.Integer, default=0)
    reply = db.Column(db.Text)  # Management response
    reply_date = db.Column(db.DateTime)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', back_populates='reviews')
    room = db.relationship('Room', back_populates='reviews')
    booking = db.relationship('Booking', back_populates='review')
    helpful_users = db.relationship('User', secondary='review_helpful_votes', 
                                  backref='helpful_reviews')
    
    # Add constraint for rating range
    __table_args__ = (
        CheckConstraint('rating >= 1 AND rating <= 5', name='check_rating_range'),
        CheckConstraint('cleanliness_rating >= 1 AND cleanliness_rating <= 5', name='check_cleanliness_range'),
        CheckConstraint('comfort_rating >= 1 AND comfort_rating <= 5', name='check_comfort_range'),
        CheckConstraint('location_rating >= 1 AND location_rating <= 5', name='check_location_range'),
        CheckConstraint('amenities_rating >= 1 AND amenities_rating <= 5', name='check_amenities_range'),
        CheckConstraint('service_rating >= 1 AND service_rating <= 5', name='check_service_range'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_name': self.user.name,
            'user_avatar': self.get_user_avatar(),
            'rating': self.rating,
            'title': self.title,
            'comment': self.comment,
            'cleanliness_rating': self.cleanliness_rating,
            'comfort_rating': self.comfort_rating,
            'location_rating': self.location_rating,
            'amenities_rating': self.amenities_rating,
            'service_rating': self.service_rating,
            'is_verified': self.is_verified,
            'helpful_count': self.helpful_count,
            'reply': self.reply,
            'reply_date': self.reply_date.strftime('%B %d, %Y') if self.reply_date else None,
            'created_at': self.created_at.strftime('%B %d, %Y'),
            'time_ago': self.get_time_ago(),
            'detailed_ratings': self.get_detailed_ratings_dict()
        }
    
    def get_user_avatar(self):
        """Generate user avatar based on name"""
        if self.user.name:
            return self.user.name[0].upper()
        return 'U'
    
    def get_time_ago(self):
        """Get human-readable time difference"""
        now = datetime.utcnow()
        diff = now - self.created_at
        
        if diff.days > 365:
            years = diff.days // 365
            return f'{years} year{"s" if years > 1 else ""} ago'
        elif diff.days > 30:
            months = diff.days // 30
            return f'{months} month{"s" if months > 1 else ""} ago'
        elif diff.days > 0:
            return f'{diff.days} day{"s" if diff.days > 1 else ""} ago'
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f'{hours} hour{"s" if hours > 1 else ""} ago'
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f'{minutes} minute{"s" if minutes > 1 else ""} ago'
        else:
            return 'Just now'
    
    def get_detailed_ratings_dict(self):
        """Get detailed ratings as dictionary"""
        return {
            'cleanliness': self.cleanliness_rating,
            'comfort': self.comfort_rating,
            'location': self.location_rating,
            'amenities': self.amenities_rating,
            'service': self.service_rating
        }
    
    def get_average_detailed_rating(self):
        """Calculate average of detailed ratings"""
        ratings = [
            self.cleanliness_rating,
            self.comfort_rating,
            self.location_rating,
            self.amenities_rating,
            self.service_rating
        ]
        return sum(ratings) / len(ratings)
    
    def mark_helpful(self, user_id):
        """Mark review as helpful by user"""
        if user_id not in [u.id for u in self.helpful_users]:
            self.helpful_count += 1
            # Add user to helpful_users relationship
            from models.user import User
            user = User.query.get(user_id)
            if user:
                self.helpful_users.append(user)
            return True
        return False
    
    def __repr__(self):
        return f'<Review {self.id} - Rating: {self.rating}>'

# Association table for helpful votes
review_helpful_votes = db.Table('review_helpful_votes',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('review_id', db.Integer, db.ForeignKey('reviews.id'), primary_key=True),
    db.Column('created_at', db.DateTime, default=datetime.utcnow)
)