from app import db
from datetime import datetime

class Payment(db.Model):
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(50), nullable=False)  # razorpay, cash, card
    payment_id = db.Column(db.String(100))  # Gateway payment ID
    payment_status = db.Column(db.String(20), default='pending')  # pending, completed, failed, refunded
    razorpay_order_id = db.Column(db.String(100))
    razorpay_payment_id = db.Column(db.String(100))
    razorpay_signature = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'booking_id': self.booking_id,
            'amount': float(self.amount),
            'payment_method': self.payment_method,
            'payment_status': self.payment_status,
            'created_at': self.created_at.isoformat()
        }
    
    def __repr__(self):
        return f'<Payment {self.id} - {self.payment_status}>'