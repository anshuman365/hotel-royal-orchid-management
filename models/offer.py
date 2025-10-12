# models/offer.py - Updated with new fields and methods
from app import db
from datetime import datetime, date
from sqlalchemy import and_, or_
import json

class Offer(db.Model):
    __tablename__ = 'offers'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    discount_type = db.Column(db.String(20), nullable=False)  # percentage, fixed, stay_x_pay_y, free_night
    discount_value = db.Column(db.Float, nullable=False)
    min_amount = db.Column(db.Float, default=0.0)
    max_discount = db.Column(db.Float)
    valid_from = db.Column(db.DateTime, default=datetime.utcnow)
    valid_until = db.Column(db.DateTime, nullable=False)
    usage_limit = db.Column(db.Integer)  # Total usage limit
    used_count = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    is_public = db.Column(db.Boolean, default=True)  # Show in public listings
    
    # Enhanced targeting criteria
    target_rooms = db.Column(db.Text)  # JSON string of room IDs or types
    target_user_type = db.Column(db.String(20), default='all')  # new_user, returning_user, vip, all
    min_stay_nights = db.Column(db.Integer, default=1)
    max_stay_nights = db.Column(db.Integer)  # Maximum stay nights
    advance_booking_days = db.Column(db.Integer, default=0)  # Minimum days in advance
    max_advance_booking_days = db.Column(db.Integer)  # Maximum days in advance
    season_type = db.Column(db.String(20), default='all')  # peak, off_peak, festival, all
    day_of_week = db.Column(db.String(20), default='all')  # weekend, weekday, all
    
    # New fields for enhanced offer system
    priority = db.Column(db.Integer, default=1)  # Higher priority offers shown first
    auto_apply = db.Column(db.Boolean, default=False)  # Auto-apply for eligible users
    banner_image = db.Column(db.String(255))  # Offer banner image
    terms_conditions = db.Column(db.Text)  # Terms and conditions
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def is_valid(self, user=None, booking_data=None, room=None):
        """Enhanced validation with more context"""
        if not self.is_active:
            return False, "Offer is not active"
        
        now = datetime.utcnow()
        if not (self.valid_from <= now <= self.valid_until):
            return False, "Offer has expired"
        
        if self.usage_limit and self.used_count >= self.usage_limit:
            return False, "Offer usage limit reached"
        
        # User-specific validations
        if user and self.target_user_type != 'all':
            if not self.is_valid_for_user(user):
                return False, "Offer not applicable for your account type"
        
        # Booking context validations
        if booking_data:
            if not self.is_valid_for_booking(booking_data):
                return False, "Offer not applicable for this booking"
        
        # Room-specific validations
        if room and self.target_rooms:
            if not self.is_valid_for_room(room):
                return False, "Offer not applicable for this room"
        
        return True, "Valid"
    
    def is_valid_for_user(self, user):
        """Enhanced user validation"""
        from models.booking import Booking
        
        if self.target_user_type == 'all':
            return True
        elif self.target_user_type == 'new_user':
            completed_bookings = Booking.query.filter_by(
                user_id=user.id, 
                status='completed'
            ).count()
            return completed_bookings == 0
        elif self.target_user_type == 'returning_user':
            completed_bookings = Booking.query.filter_by(
                user_id=user.id, 
                status='completed'
            ).count()
            return completed_bookings >= 1
        elif self.target_user_type == 'vip':
            completed_bookings = Booking.query.filter_by(
                user_id=user.id, 
                status='completed'
            ).count()
            return completed_bookings >= 3
        
        return False
    
    def is_valid_for_booking(self, booking_data):
        """Enhanced booking validation"""
        check_in = booking_data.get('check_in')
        check_out = booking_data.get('check_out')
        total_amount = booking_data.get('total_amount', 0)
        
        # Minimum amount check
        if total_amount < self.min_amount:
            return False
        
        # Stay duration validation
        if check_in and check_out:
            nights = (check_out - check_in).days
            
            if nights < self.min_stay_nights:
                return False
            
            if self.max_stay_nights and nights > self.max_stay_nights:
                return False
        
        # Advance booking validation
        if check_in and self.advance_booking_days > 0:
            days_in_advance = (check_in - date.today()).days
            if days_in_advance < self.advance_booking_days:
                return False
            
            if self.max_advance_booking_days and days_in_advance > self.max_advance_booking_days:
                return False
        
        # Season type validation
        if self.season_type != 'all' and check_in:
            if not self.is_valid_season(check_in):
                return False
        
        # Day of week validation
        if self.day_of_week != 'all' and check_in:
            if not self.is_valid_day(check_in):
                return False
        
        return True
    
    def is_valid_for_room(self, room):
        """Check if offer is valid for specific room"""
        if not self.target_rooms:
            return True
        
        try:
            target_data = json.loads(self.target_rooms)
            room_types = target_data.get('room_types', [])
            room_ids = target_data.get('room_ids', [])
            
            # Check room type
            if room_types and room.room_type in room_types:
                return True
            
            # Check room ID
            if room_ids and room.id in room_ids:
                return True
            
            return False
        except:
            return True
    
    def calculate_discount(self, amount, nights=1):
        """Enhanced discount calculation"""
        if self.discount_type == 'percentage':
            discount = amount * (self.discount_value / 100)
            if self.max_discount:
                discount = min(discount, self.max_discount)
        elif self.discount_type == 'fixed':
            discount = min(self.discount_value, amount)
        elif self.discount_type == 'stay_x_pay_y':
            discount = self.calculate_stay_x_pay_y_discount(amount, nights)
        elif self.discount_type == 'free_night':
            discount = self.calculate_free_night_discount(amount, nights)
        else:
            discount = 0
        
        return round(discount, 2)
    
    def calculate_stay_x_pay_y_discount(self, amount, nights):
        """Calculate discount for stay X pay Y offers"""
        # Example: stay 4 pay 3 means pay for 3 nights out of 4
        if self.discount_value >= nights:
            return 0
        
        nightly_rate = amount / nights
        free_nights = self.discount_value  # Actually represents the pattern
        # For stay 4 pay 3, discount = 1 night free
        if nights >= 4:  # Example threshold
            return nightly_rate
        return 0
    
    def calculate_free_night_discount(self, amount, nights):
        """Calculate discount for free night offers"""
        # Example: get 1 night free on 3+ night stay
        nightly_rate = amount / nights
        min_nights = self.min_stay_nights
        
        if nights >= min_nights:
            free_nights = int(nights / min_nights)  # 1 free night per min_nights stayed
            return free_nights * nightly_rate
        
        return 0
    
    def get_applicable_rooms(self):
        """Get list of rooms this offer applies to"""
        if not self.target_rooms:
            from models.room import Room
            return Room.query.filter_by(status='available').all()
        
        try:
            target_data = json.loads(self.target_rooms)
            room_types = target_data.get('room_types', [])
            room_ids = target_data.get('room_ids', [])
            
            from models.room import Room
            query = Room.query.filter_by(status='available')
            
            if room_types:
                query = query.filter(Room.room_type.in_(room_types))
            if room_ids:
                query = query.filter(Room.id.in_(room_ids))
            
            return query.all()
        except:
            from models.room import Room
            return Room.query.filter_by(status='available').all()
    
    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'description': self.description,
            'discount_type': self.discount_type,
            'discount_value': float(self.discount_value),
            'min_amount': float(self.min_amount) if self.min_amount else None,
            'max_discount': float(self.max_discount) if self.max_discount else None,
            'valid_from': self.valid_from.isoformat() if self.valid_from else None,
            'valid_until': self.valid_until.isoformat(),
            'is_active': self.is_active,
            'is_public': self.is_public,
            'usage_limit': self.usage_limit,
            'used_count': self.used_count,
            'min_stay_nights': self.min_stay_nights,
            'priority': self.priority,
            'auto_apply': self.auto_apply,
            'banner_image': self.banner_image
        }
    
    def increment_usage(self):
        """Increment usage count"""
        self.used_count += 1
        db.session.commit()
    
    @classmethod
    def get_available_offers(cls, user=None, booking_data=None, room=None):
        """Get all available offers with enhanced filtering"""
        offers = cls.query.filter_by(is_active=True, is_public=True).order_by(cls.priority.desc()).all()
        available_offers = []
        
        for offer in offers:
            is_valid, message = offer.is_valid(user, booking_data, room)
            if is_valid:
                available_offers.append(offer)
        
        return available_offers
    
    @classmethod
    def get_auto_apply_offers(cls, user=None, booking_data=None, room=None):
        """Get offers that should be auto-applied"""
        offers = cls.get_available_offers(user, booking_data, room)
        return [offer for offer in offers if offer.auto_apply]
    
    def __repr__(self):
        return f'<Offer {self.code}>'