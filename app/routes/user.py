from flask import Blueprint, jsonify, request
from app.models.user import User
from app.models.user_profile import UserProfile
from app.utils.jwt_handler import JWTHandler
import logging

user_bp = Blueprint('user', __name__, url_prefix='/api/users')
logger = logging.getLogger(__name__)

# ============================================================
# HELPER FUNCTION: Get user_id from JWT token
# ============================================================

def get_user_id_from_token(request):
    """
    Extract and verify user_id from Authorization header
    
    Returns:
        user_id (int) if valid, None if invalid/missing
    """
    token = JWTHandler.extract_token_from_header(request)
    if not token:
        return None
    
    user_id = JWTHandler.verify_token(token)
    return user_id


# ============================================================
# ENDPOINT 1: GET USER PROFILE (with medical info)
# ============================================================

@user_bp.route('/profile', methods=['GET'])
def user_profile():
    """
    GET: Get logged-in user's complete profile (basic + medical)
    
    URL: GET /api/users/profile
    Auth: Required (Bearer token)
    
    Returns: 
        - User basic info (name, email, phone)
        - User profile info (learning style, etc)
        - Medical info (age, diagnoses, conditions, etc)
    """
    try:
        # Verify token and get user_id
        user_id = get_user_id_from_token(request)
        if user_id is None:
            return jsonify({
                'success': False,
                'message': 'Invalid or expired token'
            }), 401
        
        # Get user basic info
        user = User.get_user_by_id(user_id)
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404
        
        # Get user profile
        profile = UserProfile.get_profile_by_user(user_id)
        
        logger.info(f"Profile retrieved for user: {user_id}")
        
        return jsonify({
            'success': True,
            'message': 'Profile retrieved successfully',
            'data': {
                'user_id': user['id'],
                'name': user['name'],
                'email': user['email'],
                'phone_number': user['phone_number'],
                'parent_user_id': user.get('parent_user_id'),
                'profile': profile if profile else None
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting user profile: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500



