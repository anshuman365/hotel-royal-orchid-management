from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from itsdangerous import URLSafeTimedSerializer
from app import db
from models.user import User
from models.booking import Booking
from utils.email_service import send_welcome_email, send_password_reset, send_login_detected
from utils.sms_service import send_otp_sms
from datetime import datetime
import secrets

auth_bp = Blueprint('auth', __name__)

def generate_reset_token(email):
    """Generate password reset token"""
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return serializer.dumps(email, salt='password-reset-salt')

def verify_reset_token(token, expiration=600):
    """Verify password reset token (10 minutes)"""
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = serializer.loads(token, salt='password-reset-salt', max_age=expiration)
        return email
    except:
        return False

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login with login detection"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember_me = bool(request.form.get('remember_me'))
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            if user.is_active:
                login_user(user, remember=remember_me)
                
                # Send login detection email
                try:
                    send_login_detected(
                        user=user,
                        login_time=datetime.now(),
                        ip_address=request.remote_addr,
                        device=request.headers.get('User-Agent', 'Unknown device')
                    )
                except Exception as e:
                    print(f"Login detection email failed: {e}")
                
                next_page = request.args.get('next')
                
                # Redirect based on user role
                if user.is_admin():
                    return redirect(next_page or url_for('admin.dashboard'))
                elif user.is_staff():
                    return redirect(next_page or url_for('admin.dashboard'))
                else:
                    return redirect(next_page or url_for('main.index'))
                
                flash(f'Welcome back, {user.name}!', 'success')
            else:
                flash('Your account has been deactivated.', 'danger')
        else:
            flash('Invalid email or password.', 'danger')
    
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validation
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return render_template('auth/register.html')
        
        # Create user
        user = User(name=name, email=email, phone=phone, role='guest')
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        # Send welcome email
        try:
            send_welcome_email(user)
        except Exception as e:
            print(f"Welcome email failed: {e}")
            # Don't fail registration if email fails
        
        # Send welcome SMS if phone provided
        if phone:
            try:
                send_otp_sms(phone, "Welcome to Hotel Royal Orchid! Your account has been created successfully.")
            except Exception as e:
                print(f"Welcome SMS failed: {e}")
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))

@auth_bp.route('/profile')
@login_required
def profile():
    """User profile"""
    user_bookings = Booking.query.filter_by(user_id=current_user.id).order_by(Booking.created_at.desc()).all()
    return render_template('auth/profile.html', bookings=user_bookings)

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Forgot password - send reset email"""
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        
        if user:
            # Generate reset token
            token = generate_reset_token(user.email)
            reset_url = url_for('auth.reset_password', token=token, _external=True)
            
            # Send reset email
            try:
                send_password_reset(user, reset_url)
                flash('Password reset instructions have been sent to your email.', 'success')
            except Exception as e:
                print(f"Password reset email failed: {e}")
                flash('Failed to send reset email. Please try again.', 'danger')
        else:
            flash('No account found with that email address.', 'danger')
    
    return render_template('auth/forgot_password.html')

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Reset password with token"""
    email = verify_reset_token(token)
    
    if not email:
        flash('Invalid or expired reset link. Please request a new one.', 'danger')
        return redirect(url_for('auth.forgot_password'))
    
    user = User.query.filter_by(email=email).first()
    
    if not user:
        flash('Invalid reset token.', 'danger')
        return redirect(url_for('auth.forgot_password'))
    
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/reset_password.html', token=token)
        
        if len(password) < 8:
            flash('Password must be at least 8 characters long.', 'danger')
            return render_template('auth/reset_password.html', token=token)
        
        # Set new password
        user.set_password(password)
        db.session.commit()
        
        flash('Your password has been reset successfully. Please login with your new password.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password.html', token=token)
