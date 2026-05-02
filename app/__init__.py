from flask import Flask, request, jsonify, redirect, url_for, make_response
from flask_cors import CORS
import logging
from app.config import Config
from app.utils.email_service import mail

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app():
    """
    Application factory pattern for Flask app
    
    Returns:
        Flask application instance
    """
    
    # Create Flask app
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(Config)
    
    # Enable CORS for web frontend
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Initialize Flask-Mail
    mail.init_app(app)

    
    # Register blueprints (routes)
    from app.routes.auth import auth_bp
    from app.routes.user import user_bp
    from app.routes.otp import otp_bp
    from app.routes.family import family_bp
    from app.routes.chatbot import chatbot_bp
    from app.routes.pages import pages_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(otp_bp)
    app.register_blueprint(family_bp)
    app.register_blueprint(chatbot_bp)
    app.register_blueprint(pages_bp)

        
    # Health check endpoint
    @app.route('/api/health', methods=['GET'])
    def health_check():
        return {
            'status': 'healthy',
            'message': 'App is running'
        }, 200
    
    @app.route('/set-lang/<lang>')
    def set_language(lang):
        if lang not in ['ar', 'en']:
            lang = 'ar'  # fallback to Arabic

    # Redirect back to the page user came from (or to register if no referrer)
        response = make_response(redirect(request.referrer or url_for('register_page')))

    # Set cookie for 1 year
        response.set_cookie('lang', lang, max_age=31536000, httponly=True, samesite='Lax')

        return response


    

    logger.info("Flask app created successfully")
    
    return app
