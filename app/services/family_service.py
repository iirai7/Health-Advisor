from app.models.user import User
from app.utils.jwt_handler import JWTHandler
from app.utils.email_service import generate_otp, send_member_welcome_email
import random
import string
import logging

logger = logging.getLogger(__name__)


def generate_password(length=10):
    """Generate a random strong password"""
    chars = string.ascii_letters + string.digits + "!@#$%"
    return ''.join(random.choices(chars, k=length))


class FamilyService:
    """Business logic for family member management"""

    @staticmethod
    def add_member(parent_user_id, name, email, relation, phone_number=None):
        """
        Add a family member:
        - Creates a new user account with auto-generated password
        - Links it to the parent user
        - Sends a welcome email with credentials

        Args:
            parent_user_id (int): The ID of the primary account owner
            name (str): Family member's full name
            email (str): Family member's email (used as username)
            relation (str): Relation to primary user (e.g. Wife, Son)
            phone_number (str): Optional phone number

        Returns:
            dict: result with success status
        """
        try:
            # Validate inputs
            if not name or len(name) < 2:
                return {'success': False, 'message': 'Name must be at least 2 characters'}

            if not email or '@' not in email:
                return {'success': False, 'message': 'Valid email is required'}

            if not relation:
                return {'success': False, 'message': 'Relation is required'}

            # Check if email already exists
            if User.email_exists(email):
                return {'success': False, 'message': 'A user with this email already exists'}

            # Get parent user info for the email
            parent_user = User.get_user_by_id(parent_user_id)
            if not parent_user:
                return {'success': False, 'message': 'Primary account not found'}

            # Auto-generate password
            auto_password = generate_password()

            # Create the user account for the family member
            member_id, msg = User.create_family_member(
                name=name,
                email=email,
                password=auto_password,
                phone_number=phone_number,
                parent_user_id=parent_user_id,
                relation=relation
            )

            if member_id is None:
                return {'success': False, 'message': msg}

            logger.info(f"Family member created: user_id={member_id}, parent={parent_user_id}")

            # Send welcome email with credentials
            sent, send_msg = send_member_welcome_email(
                to_email=email,
                member_name=name,
                parent_name=parent_user['name'],
                auto_password=auto_password,
                relation=relation
            )

            if not sent:
                logger.warning(f"Member account created but email failed: {send_msg}")
                return {
                    'success': True,
                    'message': 'Member added but email notification failed.',
                    'member_id': member_id,
                    'warning': send_msg
                }

            return {
                'success': True,
                'message': f'{name} has been added as a family member and notified by email.',
                'member_id': member_id
            }

        except Exception as e:
            logger.error(f"Add member error: {str(e)}")
            return {'success': False, 'message': f'Error adding family member: {str(e)}'}

    @staticmethod
    def get_members(parent_user_id):
        """
        Get all family members for a primary user

        Returns:
            dict: result with list of family members
        """
        try:
            members = User.get_family_members(parent_user_id)
            return {
                'success': True,
                'message': 'Family members retrieved successfully',
                'data': members if members else []
            }
        except Exception as e:
            logger.error(f"Get members error: {str(e)}")
            return {'success': False, 'message': f'Error fetching family members: {str(e)}'}

    @staticmethod
    def delete_member(parent_user_id, member_user_id):
        """
        Delete a family member account (only if it belongs to this parent)

        Returns:
            dict: result with success status
        """
        try:
            success, msg = User.delete_family_member(parent_user_id, member_user_id)
            return {'success': success, 'message': msg}
        except Exception as e:
            logger.error(f"Delete member error: {str(e)}")
            return {'success': False, 'message': f'Error deleting family member: {str(e)}'}
