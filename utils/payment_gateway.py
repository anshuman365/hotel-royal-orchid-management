import razorpay
from flask import current_app
import json

def get_razorpay_client():
    """Get Razorpay client instance"""
    key_id = current_app.config['RAZORPAY_KEY_ID']
    key_secret = current_app.config['RAZORPAY_KEY_SECRET']
    
    print(f"Razorpay Key ID: {key_id[:8]}...")  # Debug: show first 8 chars
    print(f"Razorpay Key Secret: {key_secret[:8]}...")  # Debug: show first 8 chars
    
    return razorpay.Client(auth=(key_id, key_secret))

def create_razorpay_order(amount, currency='INR', receipt=None):
    """Create Razorpay order for payment"""
    client = get_razorpay_client()
    
    data = {
        'amount': int(amount * 100),  # Convert to paise
        'currency': currency,
        'payment_capture': 1  # Auto capture payment
    }
    
    if receipt:
        data['receipt'] = receipt
    
    print(f"Creating Razorpay order with data: {data}")  # Debug
    
    try:
        order = client.order.create(data=data)
        print(f"Razorpay order created: {order}")  # Debug
        return order
    except Exception as e:
        print(f"Razorpay order creation error: {e}")
        return None

def verify_payment_signature(order_id, payment_id, signature):
    """Verify payment signature for security"""
    client = get_razorpay_client()
    
    print(f"Verifying payment - Order ID: {order_id}, Payment ID: {payment_id}, Signature: {signature}")  # Debug
    
    try:
        client.utility.verify_payment_signature({
            'razorpay_order_id': order_id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature': signature
        })
        print("Payment signature verified successfully")  # Debug
        return True
    except razorpay.errors.SignatureVerificationError as e:
        print(f"Signature verification failed: {e}")  # Debug
        return False
    except Exception as e:
        print(f"Payment verification error: {e}")
        return False

def capture_payment(payment_id, amount):
    """Capture authorized payment"""
    client = get_razorpay_client()
    
    try:
        payment = client.payment.capture(payment_id, amount)
        return payment
    except Exception as e:
        print(f"Payment capture error: {e}")
        return None

def get_payment_details(payment_id):
    """Get payment details from Razorpay"""
    client = get_razorpay_client()
    
    try:
        payment = client.payment.fetch(payment_id)
        return payment
    except Exception as e:
        print(f"Payment fetch error: {e}")
        return None