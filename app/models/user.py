from app.database import db
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
import logging

logger = logging.getLogger(__name__)

class User:
    """User model - Authentication and basic user information"""
    
    @staticmethod
    def create_user(name, email, password, phone_number=None):
        """
        Create a new user
        
        Args:
            name (str): User's full name (required)
            email (str): User's email address (required, unique)
            password (str): User's password (required)
            phone_number (str): User's phone number (optional)
        
        Returns:
            tuple: (user_id, message) - user_id if success, None if failed
        """
        try:
            cursor = db.get_cursor()
            connection = db.get_connection()
            
            # Check if email already exists
            cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
            existing_email = cursor.fetchone()
            
            if existing_email:
                return None, "Email already exists"
            
            # Validate phone_number if provided
            if phone_number and len(phone_number) < 7:
                return None, "Phone number must be at least 7 characters"
            
            # Hash password using PBKDF2:SHA256
            hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
            
            # Insert user into database
            cursor.execute("""
                INSERT INTO users (name, email, password, phone_number, created_at)
                VALUES (%s, %s, %s, %s, %s)
            """, (name, email, hashed_password, phone_number, datetime.datetime.now()))
            
            connection.commit()
            
            # Get the newly created user ID
            cursor.execute("SELECT LAST_INSERT_ID() as id")
            result = cursor.fetchone()
            user_id = result['id'] if result else None
            
            logger.info(f"User created successfully: {user_id}")
            return user_id, "User created successfully"
        
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating user: {str(e)}")
            return None, f"Error creating user: {str(e)}"
    
    @staticmethod
    def get_user_by_email(email):
        """
        Get user by email
        
        Returns:
            dict: User data including is_verified, or None if not found
        """
        try:
            cursor = db.get_cursor()
            cursor.execute(
                "SELECT id, name, email, password, is_verified FROM users WHERE email = %s",
                (email,)
            )
            user = cursor.fetchone()
            return user
        except Exception as e:
            logger.error(f"Error getting user by email: {str(e)}")
            return None
    
    @staticmethod
    def get_user_by_id(user_id):
        """
        Get user by ID
        
        Returns:
            dict: User data with id, name, email, phone_number or None if not found
        """
        try:
            cursor = db.get_cursor()
            cursor.execute(
                "SELECT id, name, email, phone_number, parent_user_id, relation FROM users WHERE id = %s",
                (user_id,)
            )
            user = cursor.fetchone()
            return user
        except Exception as e:
            logger.error(f"Error getting user by ID: {str(e)}")
            return None
    
    @staticmethod
    def verify_password(stored_password_hash, provided_password):
        """Verify password against stored hash"""
        try:
            return check_password_hash(stored_password_hash, provided_password)
        except Exception as e:
            logger.error(f"Error verifying password: {str(e)}")
            return False
    
    @staticmethod
    def email_exists(email):
        """Check if email already exists in database"""
        try:
            cursor = db.get_cursor()
            cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
            result = cursor.fetchone()
            return result is not None
        except Exception as e:
            logger.error(f"Error checking email existence: {str(e)}")
            return False
    
    @staticmethod
    def update_password(user_id, new_password):
        """Update user's password"""
        try:
            if not new_password or len(new_password) < 6:
                return False, "Password must be at least 6 characters"
            
            cursor = db.get_cursor()
            connection = db.get_connection()
            
            hashed_password = generate_password_hash(new_password, method='pbkdf2:sha256')
            
            cursor.execute("""
                UPDATE users 
                SET password = %s, updated_at = NOW()
                WHERE id = %s
            """, (hashed_password, user_id))
            
            connection.commit()
            
            logger.info(f"Password updated for user: {user_id}")
            return True, "Password updated successfully"
        
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating password: {str(e)}")
            return False, f"Error updating password: {str(e)}"

    # ============================================================
    # OTP METHODS
    # ============================================================

    @staticmethod
    def save_otp(user_id, otp_code):
        """
        Save OTP and set expiry to 10 minutes from now
        
        Returns:
            tuple: (success, message)
        """
        try:
            cursor = db.get_cursor()
            connection = db.get_connection()
            expires_at = datetime.datetime.now() + datetime.timedelta(minutes=10)
            cursor.execute("""
                UPDATE users
                SET otp = %s, otp_expires_at = %s
                WHERE id = %s
            """, (otp_code, expires_at, user_id))
            connection.commit()
            logger.info(f"OTP saved for user: {user_id}")
            return True, "OTP saved"
        except Exception as e:
            db.rollback()
            logger.error(f"Error saving OTP: {str(e)}")
            return False, f"Error saving OTP: {str(e)}"

    @staticmethod
    def verify_otp(email, otp_code, check_verified=True):
        """
        Verify the OTP for a given email
        
        Args:
            email (str): User's email
            otp_code (str): OTP code to verify
            check_verified (bool): If True, returns error if account already verified (for signup)
                                   If False, skips this check (for password reset)
        
        Returns:
            tuple: (success, message)
        """
        try:
            cursor = db.get_cursor()
            cursor.execute(
                "SELECT id, otp, otp_expires_at, is_verified FROM users WHERE email = %s",
                (email,)
            )
            user = cursor.fetchone()

            if not user:
                return False, "User not found"

            if check_verified and user['is_verified']:
                return False, "Account is already verified"

            if user['otp'] != otp_code:
                return False, "Invalid OTP"

            if not user['otp_expires_at'] or datetime.datetime.now() > user['otp_expires_at']:
                return False, "OTP has expired"

            return True, "OTP is valid"

        except Exception as e:
            logger.error(f"Error verifying OTP: {str(e)}")
            return False, f"Error verifying OTP: {str(e)}"

    @staticmethod
    def mark_verified(user_id):
        """
        Mark user account as verified and clear OTP fields
        
        Returns:
            tuple: (success, message)
        """
        try:
            cursor = db.get_cursor()
            connection = db.get_connection()
            cursor.execute("""
                UPDATE users
                SET is_verified = TRUE, otp = NULL, otp_expires_at = NULL
                WHERE id = %s
            """, (user_id,))
            connection.commit()
            logger.info(f"User {user_id} marked as verified")
            return True, "Account verified successfully"
        except Exception as e:
            db.rollback()
            logger.error(f"Error marking user verified: {str(e)}")
            return False, f"Error: {str(e)}"

    # ============================================================
    # FAMILY MEMBER METHODS
    # ============================================================

    @staticmethod
    def create_family_member(name, email, password, phone_number, parent_user_id, relation):
        """
        Create a new family member user linked to a parent account.
        
        Returns:
            tuple: (user_id, message)
        """
        try:
            cursor = db.get_cursor()
            connection = db.get_connection()
            
            # Hash password
            hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
            
            # Insert family member into database, marked as verified automatically
            cursor.execute("""
                INSERT INTO users (name, email, password, phone_number, is_verified, parent_user_id, relation, created_at)
                VALUES (%s, %s, %s, %s, TRUE, %s, %s, %s)
            """, (name, email, hashed_password, phone_number, parent_user_id, relation, datetime.datetime.now()))
            
            connection.commit()
            
            # Get the newly created user ID
            cursor.execute("SELECT LAST_INSERT_ID() as id")
            result = cursor.fetchone()
            user_id = result['id'] if result else None
            
            logger.info(f"Family member created successfully: {user_id} for parent: {parent_user_id}")
            return user_id, "Family member created successfully"
        
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating family member: {str(e)}")
            return None, f"Error creating family member: {str(e)}"

    @staticmethod
    def get_family_members(parent_user_id):
        """
        Get all family members for a specific parent user.
        
        Returns:
            list: List of dictionaries with family member data
        """
        try:
            cursor = db.get_cursor()
            cursor.execute("""
                SELECT id, name, email, phone_number, relation, created_at
                FROM users 
                WHERE parent_user_id = %s
            """, (parent_user_id,))
            
            members = cursor.fetchall()
            return members if members else []
        
        except Exception as e:
            logger.error(f"Error getting family members: {str(e)}")
            return []

    @staticmethod
    def delete_family_member(parent_user_id, member_user_id):
        """
        Delete a family member account. Ensures the member belongs to the parent.
        
        Returns:
            tuple: (success, message)
        """
        try:
            cursor = db.get_cursor()
            connection = db.get_connection()
            
            # Check if member belongs to parent
            cursor.execute("""
                SELECT id FROM users 
                WHERE id = %s AND parent_user_id = %s
            """, (member_user_id, parent_user_id))
            
            member = cursor.fetchone()
            if not member:
                return False, "Family member not found or does not belong to you"
            
            # Delete member
            cursor.execute("DELETE FROM users WHERE id = %s", (member_user_id,))
            connection.commit()
            
            logger.info(f"Family member {member_user_id} deleted by parent {parent_user_id}")
            return True, "Family member deleted successfully"
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting family member: {str(e)}")
            return False, f"Error deleting family member: {str(e)}"

    @staticmethod
    def clear_otp(user_id):
        """
        Clear OTP fields for a user (after successful verification/reset)
        
        Returns:
            tuple: (success, message)
        """
        try:
            cursor = db.get_cursor()
            connection = db.get_connection()
            cursor.execute("""
                UPDATE users
                SET otp = NULL, otp_expires_at = NULL
                WHERE id = %s
            """, (user_id,))
            connection.commit()
            return True, "OTP cleared successfully"
        except Exception as e:
            db.rollback()
            logger.error(f"Error clearing OTP: {str(e)}")
            return False, f"Error: {str(e)}"
