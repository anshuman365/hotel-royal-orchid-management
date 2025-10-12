from flask_mail import Message
from flask import render_template, current_app
from app import mail
from threading import Thread
import html2text

def send_async_email(app, msg):
    """Send email asynchronously"""
    with app.app_context():
        try:
            mail.send(msg)
        except Exception as e:
            print(f"Email sending failed: {e}")

def send_email(subject, recipients, text_body, html_body):
    """Send email with both text and HTML versions"""
    msg = Message(
        subject=subject,
        sender=current_app.config['MAIL_DEFAULT_SENDER'],
        recipients=recipients
    )
    msg.body = text_body
    msg.html = html_body
    Thread(target=send_async_email, args=(current_app._get_current_object(), msg)).start()

def html_to_text(html_content):
    """Convert HTML to plain text"""
    h = html2text.HTML2Text()
    h.ignore_links = False
    h.ignore_images = True
    return h.handle(html_content)

def send_booking_confirmation(booking, customer_email):
    """Send booking confirmation email"""
    subject = f"Booking Confirmation - #{booking.id} - Hotel Royal Orchid"
    
    html_body = render_template('emails/booking_confirmation.html', booking=booking)
    text_body = render_template('emails/booking_confirmation.txt', booking=booking)
    
    send_email(
        subject=subject,
        recipients=[customer_email],
        text_body=text_body,
        html_body=html_body
    )

def send_payment_successful(booking, payment, customer_email):
    """Send payment successful email"""
    subject = f"Payment Successful - Booking #{booking.id} - Hotel Royal Orchid"
    
    html_body = render_template('emails/payment_successful.html', booking=booking, payment=payment)
    text_body = render_template('emails/payment_successful.txt', booking=booking, payment=payment)
    
    send_email(
        subject=subject,
        recipients=[customer_email],
        text_body=text_body,
        html_body=html_body
    )

def send_payment_failed(booking, customer_email):
    """Send payment failed email"""
    subject = f"Payment Failed - Booking #{booking.id} - Hotel Royal Orchid"
    
    html_body = render_template('emails/payment_failed.html', booking=booking)
    text_body = render_template('emails/payment_failed.txt', booking=booking)
    
    send_email(
        subject=subject,
        recipients=[customer_email],
        text_body=text_body,
        html_body=html_body
    )

def send_booking_cancellation(booking, customer_email):
    """Send booking cancellation email"""
    subject = f"Booking Cancelled - #{booking.id} - Hotel Royal Orchid"
    
    html_body = render_template('emails/booking_cancellation.html', booking=booking)
    text_body = render_template('emails/booking_cancellation.txt', booking=booking)
    
    send_email(
        subject=subject,
        recipients=[customer_email],
        text_body=text_body,
        html_body=html_body
    )

def send_welcome_email(user):
    """Send welcome email to new user"""
    subject = "Welcome to Hotel Royal Orchid - Your Luxury Journey Begins"
    
    html_body = render_template('emails/welcome.html', user=user)
    text_body = render_template('emails/welcome.txt', user=user)
    
    send_email(
        subject=subject,
        recipients=[user.email],
        text_body=text_body,
        html_body=html_body
    )

def send_password_reset(user, reset_token):
    """Send password reset email"""
    subject = "Password Reset Request - Hotel Royal Orchid"
    
    html_body = render_template('emails/password_reset.html', user=user, reset_url=reset_token)
    text_body = render_template('emails/password_reset.txt', user=user, reset_url=reset_token)
    
    send_email(
        subject=subject,
        recipients=[user.email],
        text_body=text_body,
        html_body=html_body
    )

def send_login_detected(user, login_time, ip_address, device=None, location=None):
    """Send login detection email"""
    subject = f"New Login Detected - {login_time.strftime('%b %d, %Y')} - Hotel Royal Orchid"
    
    html_body = render_template('emails/login_detected.html', 
                               user=user, 
                               login_time=login_time,
                               ip_address=ip_address,
                               device=device,
                               location=location)
    text_body = render_template('emails/login_detected.txt', 
                               user=user, 
                               login_time=login_time,
                               ip_address=ip_address,
                               device=device,
                               location=location)
    
    send_email(
        subject=subject,
        recipients=[user.email],
        text_body=text_body,
        html_body=html_body
    )

def send_admin_booking_update(booking, admin_note=None):
    """Send booking update email from admin actions"""
    subject = f"Booking #{booking.id} Updated - Hotel Royal Orchid"
    
    html_body = render_template('emails/admin_booking_update.html', 
                               booking=booking,
                               admin_note=admin_note)
    text_body = render_template('emails/admin_booking_update.txt', 
                               booking=booking,
                               admin_note=admin_note)
    
    send_email(
        subject=subject,
        recipients=[booking.user.email],
        text_body=text_body,
        html_body=html_body
    )

def send_review_approved_notification(review, user_email):
    """Send email when review is approved"""
    subject = "Your Review Has Been Published! - Hotel Royal Orchid"
    
    html_body = render_template('emails/review_approved.html', review=review)
    text_body = render_template('emails/review_approved.txt', review=review)
    
    send_email(
        subject=subject,
        recipients=[user_email],
        text_body=text_body,
        html_body=html_body
    )

def send_review_rejected_notification(review, user_email, rejection_reason):
    """Send email when review is rejected"""
    subject = "Regarding Your Recent Review - Hotel Royal Orchid"
    
    html_body = render_template('emails/review_rejected.html', review=review, rejection_reason=rejection_reason)
    text_body = render_template('emails/review_rejected.txt', review=review, rejection_reason=rejection_reason)
    
    send_email(
        subject=subject,
        recipients=[user_email],
        text_body=text_body,
        html_body=html_body
    )

def send_review_reply_notification(review, user_email):
    """Send email when management replies to review"""
    subject = "Management Response to Your Review - Hotel Royal Orchid"
    
    html_body = render_template('emails/review_reply.html', review=review)
    text_body = render_template('emails/review_reply.txt', review=review)
    
    send_email(
        subject=subject,
        recipients=[user_email],
        text_body=text_body,
        html_body=html_body
    )

# Add to utils/email_service.py
def send_ai_personalized_welcome(user, booking):
    """Send AI-enhanced welcome email"""
    ai_service = OpenRouterAI()
    
    prompt = f"""
    Create a warm, personalized welcome email for a hotel guest:
    
    Guest: {user.name}
    Booking: {booking.room.name} for {booking.total_nights} nights
    Special Occasion: {booking.special_requests or 'Not specified'}
    
    Tone: Warm, professional, excited to host them
    Include: Personal welcome, anticipation of their stay, offer assistance
    Length: 2-3 short paragraphs
    """
    
    ai_content = ai_service._make_request(prompt)
    personalized_message = ai_content['choices'][0]['message']['content'] if 'choices' in ai_content else ""
    
    # Use your existing email template with AI-enhanced content
    html_body = render_template('emails/ai_welcome.html', 
                               user=user, 
                               booking=booking,
                               personalized_message=personalized_message)
    
    send_email(
        subject=f"Personalized Welcome, {user.name}! - Hotel Royal Orchid",
        recipients=[user.email],
        text_body=personalized_message,
        html_body=html_body
    )
