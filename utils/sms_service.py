import requests
from flask import current_app

def send_sms(phone_number, message):
    """Send SMS using MSG91 API"""
    if not current_app.config['MSG91_AUTH_KEY']:
        print(f"SMS would be sent to {phone_number}: {message}")
        return True
    
    try:
        url = "https://api.msg91.com/api/v2/sendsms"
        
        payload = {
            "sender": current_app.config['MSG91_SENDER_ID'],
            "route": "4",
            "country": "91",
            "sms": [
                {
                    "message": message,
                    "to": [phone_number.lstrip('+91')]
                }
            ]
        }
        
        headers = {
            "authkey": current_app.config['MSG91_AUTH_KEY'],
            "Content-Type": "application/json"
        }
        
        response = requests.post(url, json=payload, headers=headers)
        return response.status_code == 200
    except Exception as e:
        print(f"SMS sending failed: {e}")
        return False

def send_booking_sms(booking, phone_number):
    """Send booking confirmation SMS"""
    message = f"Dear Guest, your booking #{booking.id} at Hotel Royal Orchid is confirmed. Check-in: {booking.check_in}, Check-out: {booking.check_out}. Total: ₹{booking.final_amount:.2f}"
    return send_sms(phone_number, message)

def send_otp_sms(phone_number, otp):
    """Send OTP SMS"""
    message = f"Your OTP for Hotel Royal Orchid is {otp}. Valid for 10 minutes."
    return send_sms(phone_number, message)