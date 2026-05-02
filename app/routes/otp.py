from flask import Blueprint, request, jsonify
from app.models.user import User
from app.utils.email_service import generate_otp, send_otp_email
from app.utils.jwt_handler import JWTHandler
import logging

otp_bp = Blueprint('otp', __name__, url_prefix='/api/auth')
logger = logging.getLogger(__name__)


# ============================================================
# ENDPOINT 1: SEND OTP
# POST /api/auth/send-otp
# ============================================================

@otp_bp.route('/send-otp', methods=['POST'])
def send_otp():
    """
    Send OTP to a registered user's email

    Expected JSON: { "email": "user@example.com" }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400

        email = data.get('email', '').strip().lower()
        if not email:
            return jsonify({'success': False, 'message': 'Email is required'}), 400

        # Get user by email
        user = User.get_user_by_email(email)
        if not user:
            return jsonify({'success': False, 'message': 'No account found with this email'}), 404

        if user.get('is_verified'):
            return jsonify({'success': False, 'message': 'Account is already verified'}), 400

        # Generate and save OTP
        otp_code = generate_otp()
        success, msg = User.save_otp(user['id'], otp_code)
        if not success:
            return jsonify({'success': False, 'message': msg}), 500

        # Send OTP via email
        sent, send_msg = send_otp_email(email, otp_code, user['name'])
        if not sent:
            return jsonify({'success': False, 'message': send_msg}), 500

        logger.info(f"OTP sent to {email}")
        return jsonify({'success': True, 'message': 'OTP sent to your email'}), 200

    except Exception as e:
        logger.error(f"Send OTP error: {str(e)}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


# ============================================================
# ENDPOINT 2: VERIFY OTP
# POST /api/auth/verify-otp
# ============================================================

@otp_bp.route('/verify-otp', methods=['POST'])
def verify_otp():
    """
    Verify OTP and activate the account

    Expected JSON: { "email": "user@example.com", "otp": "123456" }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400

        email = data.get('email', '').strip().lower()
        otp_code = data.get('otp', '').strip()

        if not email or not otp_code:
            return jsonify({'success': False, 'message': 'Email and OTP are required'}), 400

        # Verify OTP
        valid, msg = User.verify_otp(email, otp_code)
        if not valid:
            return jsonify({'success': False, 'message': msg}), 400

        # Mark account as verified
        user = User.get_user_by_email(email)
        User.mark_verified(user['id'])

        # Generate JWT token
        token = JWTHandler.generate_token(user['id'])

        logger.info(f"User {email} verified successfully")
        return jsonify({
            'success': True,
            'message': 'Account verified successfully',
            'token': token,
            'user_id': user['id'],
            'user_name': user['name']
        }), 200

    except Exception as e:
        logger.error(f"Verify OTP error: {str(e)}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


# ============================================================
# ENDPOINT 3: RESEND OTP
# POST /api/auth/resend-otp
# ============================================================

@otp_bp.route('/resend-otp', methods=['POST'])
def resend_otp():
    """
    Resend OTP to user's email

    Expected JSON: { "email": "user@example.com" }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400

        email = data.get('email', '').strip().lower()
        if not email:
            return jsonify({'success': False, 'message': 'Email is required'}), 400

        user = User.get_user_by_email(email)
        if not user:
            return jsonify({'success': False, 'message': 'No account found with this email'}), 404

        if user.get('is_verified'):
            return jsonify({'success': False, 'message': 'Account is already verified'}), 400

        otp_code = generate_otp()
        User.save_otp(user['id'], otp_code)
        sent, send_msg = send_otp_email(email, otp_code, user['name'])

        if not sent:
            return jsonify({'success': False, 'message': send_msg}), 500

        return jsonify({'success': True, 'message': 'OTP resent to your email'}), 200

    except Exception as e:
        logger.error(f"Resend OTP error: {str(e)}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500
