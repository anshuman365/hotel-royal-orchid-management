from app import db
from datetime import datetime

class Booking(db.Model):
    __tablename__ = 'bookings'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=False)
    check_in = db.Column(db.Date, nullable=False)
    check_out = db.Column(db.Date, nullable=False)
    adults = db.Column(db.Integer, nullable=False, default=1)
    children = db.Column(db.Integer, default=0)
    total_nights = db.Column(db.Integer, nullable=False)
    base_amount = db.Column(db.Float, nullable=False)
    tax_amount = db.Column(db.Float, default=0.0)
    discount_amount = db.Column(db.Float, default=0.0)
    total_amount = db.Column(db.Float, nullable=False)
    final_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')
    payment_status = db.Column(db.String(20), default='pending')
    special_requests = db.Column(db.Text)
    coupon_code = db.Column(db.String(50))
    razorpay_order_id = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships - use back_populates consistently
    user = db.relationship('User', back_populates='bookings')
    room = db.relationship('Room', back_populates='bookings')
    review = db.relationship('Review', back_populates='booking', uselist=False)
    payments = db.relationship('Payment', backref='booking', lazy=True)
    
    def calculate_total_nights(self):
        return (self.check_out - self.check_in).days
    
    def calculate_total_amount(self, room_price):
        nights = self.calculate_total_nights()
        base = room_price * nights
        tax = base * 0.18  # 18% GST
        total = base + tax
        return base, tax, total
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'room_id': self.room_id,
            'check_in': self.check_in.isoformat(),
            'check_out': self.check_out.isoformat(),
            'adults': self.adults,
            'children': self.children,
            'total_nights': self.total_nights,
            'total_amount': float(self.total_amount),
            'final_amount': float(self.final_amount),
            'status': self.status,
            'payment_status': self.payment_status,
            'special_requests': self.special_requests
        }
    
    def __repr__(self):
        return f'<Booking {self.id} - {self.status}>'