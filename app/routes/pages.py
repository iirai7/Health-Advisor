"""
app/routes/pages.py

Renders all frontend HTML templates for the Diagnosis app.
Auth is handled client-side via JWT in localStorage.
No API logic here — only template rendering.
"""

from flask import Blueprint, render_template
import logging

logger = logging.getLogger(__name__)

pages_bp = Blueprint('pages', __name__)


# ============================================================
# PUBLIC PAGES
# ============================================================

@pages_bp.route('/', methods=['GET'])
def welcome():
    """Landing / Welcome Page"""
    logger.info("Rendering welcome page")
    return render_template('welcome.html', page='welcome')


@pages_bp.route('/login', methods=['GET'])
def login():
    """Login Page"""
    logger.info("Rendering login page")
    return render_template('login.html', page='login')


@pages_bp.route('/register', methods=['GET'])
def register():
    """Register Page"""
    logger.info("Rendering register page")
    return render_template('register.html', page='register')


@pages_bp.route('/verify-otp', methods=['GET'])
def verify_otp():
    """
    OTP Verification Page
    Shown after registration — user enters the code sent to their email.
    Email is passed as a query param: /verify-otp?email=user@example.com
    """
    logger.info("Rendering OTP verification page")
    return render_template('verify_otp.html', page='verify_otp')


@pages_bp.route('/forgot-password', methods=['GET'])
def forgot_password():
    """Forgot Password Page — user enters their email to receive OTP"""
    logger.info("Rendering forgot password page")
    return render_template('forgot_password.html', page='forgot_password')


@pages_bp.route('/reset-password', methods=['GET'])
def reset_password():
    """
    Reset Password Page
    User enters OTP + new password.
    Email passed as query param: /reset-password?email=user@example.com
    """
    logger.info("Rendering reset password page")
    return render_template('reset_password.html', page='reset_password')


# ============================================================
# PROTECTED PAGES (auth enforced client-side via api.js)
# ============================================================

@pages_bp.route('/dashboard', methods=['GET'])
def dashboard():
    """Main Dashboard — family selector, new diagnosis button, recent records"""
    logger.info("Rendering dashboard page")
    return render_template('dashboard.html', page='dashboard')


@pages_bp.route('/chatbot', methods=['GET'])
def chatbot():
    """
    Medical AI Chatbot Page
    Query param: ?member_id=X (optional — defaults to primary user)
    """
    logger.info("Rendering chatbot page")
    return render_template('chatbot.html', page='chatbot')


@pages_bp.route('/family', methods=['GET'])
def family():
    """Family Management Page — list, add, delete family members"""
    logger.info("Rendering family page")
    return render_template('family.html', page='family')


@pages_bp.route('/history', methods=['GET'])
def history():
    """
    Medical Records History Page
    Shows all past diagnosis sessions for user and family members.
    """
    logger.info("Rendering history page")
    return render_template('history.html', page='history')


@pages_bp.route('/profile', methods=['GET'])
def profile():
    """User Profile Page — view and edit basic info"""
    logger.info("Rendering profile page")
    return render_template('profile.html', page='profile')


@pages_bp.route('/settings', methods=['GET'])
def settings():
    """Settings Page — theme, language, privacy, logout, delete account"""
    logger.info("Rendering settings page")
    return render_template('settings.html', page='settings')


@pages_bp.route('/privacy', methods=['GET'])
def privacy():
    """Privacy Policy Page"""
    logger.info("Rendering privacy page")
    return render_template('privacy.html', page='privacy')


@pages_bp.route('/about', methods=['GET'])
def about():
    """About Us Page"""
    logger.info("Rendering about page")
    return render_template('about.html', page='about')


# ============================================================
# ERROR PAGES
# ============================================================

@pages_bp.route('/unauthorized', methods=['GET'])
def unauthorized():
    """401 Unauthorized — redirected here when token is missing/expired"""
    logger.warning("Rendering 401 unauthorized page")
    return render_template('401.html', page='401'), 401


@pages_bp.errorhandler(404)
def handle_404(error):
    logger.warning(f"404 error: {error}")
    return render_template('404.html', page='404'), 404


@pages_bp.errorhandler(500)
def handle_500(error):
    logger.error(f"500 error: {error}")
    return render_template('500.html', page='500'), 500