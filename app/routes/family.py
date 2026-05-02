from flask import Blueprint, request, jsonify
from app.services.family_service import FamilyService
from app.utils.jwt_handler import JWTHandler
import logging

family_bp = Blueprint('family', __name__, url_prefix='/api/family')
logger = logging.getLogger(__name__)


def get_user_id_from_token(req):
    """Extract and verify user_id from Authorization header"""
    token = JWTHandler.extract_token_from_header(req)
    if not token:
        return None
    return JWTHandler.verify_token(token)


# ============================================================
# ENDPOINT 1: ADD FAMILY MEMBER
# POST /api/family/add
# ============================================================

@family_bp.route('/add', methods=['POST'])
def add_member():
    """
    Add a family member to the primary account.
    Can be called during signup or anytime after.

    Expected JSON:
    {
        "name": "Sara Ahmed",
        "email": "sara@example.com",
        "relation": "Wife",
        "phone_number": "05512345678"  (optional)
    }
    Auth: Required (Bearer token)
    """
    try:
        user_id = get_user_id_from_token(request)
        if user_id is None:
            return jsonify({'success': False, 'message': 'Invalid or expired token'}), 401

        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400

        name = data.get('name', '').strip()
        email = data.get('email', '').strip().lower()
        relation = data.get('relation', '').strip()
        phone_number = data.get('phone_number', '').strip() or None

        result = FamilyService.add_member(
            parent_user_id=user_id,
            name=name,
            email=email,
            relation=relation,
            phone_number=phone_number
        )

        status_code = 201 if result['success'] else 400
        return jsonify(result), status_code

    except Exception as e:
        logger.error(f"Add member endpoint error: {str(e)}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


# ============================================================
# ENDPOINT 2: GET ALL FAMILY MEMBERS
# GET /api/family
# ============================================================

@family_bp.route('/', methods=['GET'])
def get_members():
    """
    Get all family members linked to the primary account.
    Auth: Required (Bearer token)
    """
    try:
        user_id = get_user_id_from_token(request)
        if user_id is None:
            return jsonify({'success': False, 'message': 'Invalid or expired token'}), 401

        result = FamilyService.get_members(user_id)
        return jsonify(result), 200

    except Exception as e:
        logger.error(f"Get members endpoint error: {str(e)}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


# ============================================================
# ENDPOINT 3: DELETE FAMILY MEMBER
# DELETE /api/family/<member_user_id>
# ============================================================

@family_bp.route('/<int:member_user_id>', methods=['DELETE'])
def delete_member(member_user_id):
    """
    Delete a family member account.
    Only the primary account owner can delete their members.
    Auth: Required (Bearer token)
    """
    try:
        user_id = get_user_id_from_token(request)
        if user_id is None:
            return jsonify({'success': False, 'message': 'Invalid or expired token'}), 401

        result = FamilyService.delete_member(
            parent_user_id=user_id,
            member_user_id=member_user_id
        )

        status_code = 200 if result['success'] else 400
        return jsonify(result), status_code

    except Exception as e:
        logger.error(f"Delete member endpoint error: {str(e)}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


# ============================================================
# ENDPOINT 4: GET FAMILY MEMBERS BY PARENT ID
# GET /api/family/parent/<parent_user_id>
# ============================================================

@family_bp.route('/parent/<int:parent_user_id>', methods=['GET'])
def get_members_by_parent(parent_user_id):
    """
    Get all family members under a specific parent user.
    Used by child accounts to see their parent's family.
    Auth: Required (Bearer token)
    """
    try:
        user_id = get_user_id_from_token(request)
        if user_id is None:
            return jsonify({'success': False, 'message': 'Invalid or expired token'}), 401

        result = FamilyService.get_members(parent_user_id)
        return jsonify(result), 200

    except Exception as e:
        logger.error(f"Get members by parent endpoint error: {str(e)}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500
