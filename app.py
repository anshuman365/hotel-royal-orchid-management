from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from config import Config
from datetime import datetime
from flask_wtf import CSRFProtect

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()
migrate = Migrate()
csrf = CSRFProtect()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    
    # Login manager configuration
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'
    
    # Register blueprints
    from blueprints.main import main_bp
    from blueprints.auth import auth_bp
    from blueprints.booking import booking_bp
    from blueprints.admin import admin_bp
    from blueprints.api import api_bp
    from blueprints.reviews import reviews_bp
    from blueprints.chatbot import chatbot_bp  # NEW IMPORT
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(booking_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(reviews_bp)
    app.register_blueprint(chatbot_bp)  # NEW REGISTRATION
    
    csrf.exempt(main_bp)
    csrf.exempt(auth_bp)
    csrf.exempt(booking_bp)
    csrf.exempt(admin_bp)
    csrf.exempt(api_bp)
    csrf.exempt(reviews_bp)
    csrf.exempt(chatbot_bp)
    
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('500.html'), 500

    @app.context_processor
    def inject_now():
        return {'now': datetime.now()}
    
    @app.template_filter('currency')
    def currency_format(value):
        """Format value as Indian currency"""
        try:
            return "₹{:,.2f}".format(float(value))
        except (ValueError, TypeError):
            return "₹0.00"
    
    return app

# Create app instance
app = create_app()

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)