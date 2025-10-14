# © 2025 Anshuman Singh. All Rights Reserved.
# Unauthorized use prohibited.
import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Basic Flask Config
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here-change-in-production'
    
    # Database Config
    basedir = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'instance', 'hotel.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Email Config
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', 'nexoraindustries@gmail.com')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', 'password')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or 'noreply@hotelroyalorchid.com'
    
    # Payment Gateway (Razorpay)
    RAZORPAY_KEY_ID = os.environ.get('RAZORPAY_KEY_ID', 'rzp_test_key')
    RAZORPAY_KEY_SECRET = os.environ.get('RAZORPAY_KEY_SECRET', 'test_secrete_key')
    RAZORPAY_WEBHOOK_SECRET = os.environ.get('RAZORPAY_WEBHOOK_SECRET', 'https://dashboard.razorpay.com/app/webhooks/random')
    
    # SMS Gateway (MSG91)
    MSG91_AUTH_KEY = os.environ.get('MSG91_AUTH_KEY') or 'key'
    MSG91_SENDER_ID = os.environ.get('MSG91_SENDER_ID') or 'HOTELR'
    
    # JWT Config
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-string'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    
    # File Upload Config
    UPLOAD_FOLDER = os.path.join(basedir, 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # Admin Config
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL') or 'admin@hotelroyalorchid.com'
    
    # AI Configuration - NEW
    OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY') or 'openrouter_API_key'
    OPENROUTER_MODEL = os.environ.get('OPENROUTER_MODEL') or 'openai/gpt-3.5-turbo'
    OPENROUTER_BASE_URL = 'https://openrouter.ai/api/v1/chat/completions'

class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    # Use PostgreSQL in production
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'