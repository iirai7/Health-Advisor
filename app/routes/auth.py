from flask import Blueprint, request, jsonify
from app.services.auth_service import AuthService
from app.utils.jwt_handler import JWTHandler
import logging

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')
logger = logging.getLogger(__name__)

# ============================================================
# ENDPOINT 1: REGISTER (with medical information)
# ============================================================

@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Register new user with medical information
    
    Expected JSON: {
        "name": "Ahmed Al-Saud",
        "email": "ahmed@example.com",
        "password": "password123",
        "phone_number": "0551234567"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'No data provided'
            }), 400
        
        # ============================================================
        # BASIC USER INFO (required)
        # ============================================================
        name = data.get('name', '').strip()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        phone_number = data.get('phone_number', '').strip()
        
        # Call service to handle all validation and creation
        result = AuthService.register(
            name=name,
            email=email,
            password=password,
            phone_number=phone_number if phone_number else None
        )
        
        if result['success']:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
    
    except Exception as e:
        logger.error(f"Register error: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error during registration: {str(e)}'
        }), 500


# ============================================================
# ENDPOINT 2: LOGIN
# ============================================================

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Login user
    
    Expected JSON: {
        "email": "ahmed@example.com",
        "password": "password123"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'No data provided'
            }), 400
        
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        # Call service
        result = AuthService.login(email, password)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 401
    
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error during login: {str(e)}'
        }), 500


# ============================================================
# ENDPOINT 3: VERIFY TOKEN
# ============================================================

@auth_bp.route('/verify-token', methods=['GET'])
def verify_token():
    """
    Verify if token is valid
    
    Expected header: Authorization: Bearer <token>
    """
    try:
        # Extract token
        token = JWTHandler.extract_token_from_header(request)
        
        # Call service
        result = AuthService.verify_token(token)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 401
    
    except Exception as e:
        logger.error(f"Token verification error: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error verifying token: {str(e)}'
        }), 500


# ============================================================
# ENDPOINT 4: FORGOT PASSWORD
# ============================================================

@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    """
    Request password reset OTP
    
    Expected JSON: { "email": "user@example.com" }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
            
        email = data.get('email', '').strip().lower()
        result = AuthService.forgot_password(email)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Forgot password endpoint error: {str(e)}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


# ============================================================
# ENDPOINT 5: RESET PASSWORD
# ============================================================

@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    """
    Reset password using OTP
    
    Expected JSON: { 
        "email": "user@example.com", 
        "otp": "123456", 
        "new_password": "newpassword123" 
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
            
        email = data.get('email', '').strip().lower()
        otp_code = data.get('otp', '').strip()
        new_password = data.get('new_password', '')
        
        result = AuthService.reset_password(email, otp_code, new_password)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Reset password endpoint error: {str(e)}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500
