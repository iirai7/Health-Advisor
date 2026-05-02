from app.models.user import User
from app.models.user_profile import UserProfile
from app.utils.jwt_handler import JWTHandler
from app.utils.email_service import generate_otp, send_otp_email, send_password_reset_email
import logging

logger = logging.getLogger(__name__)

class AuthService:
    """Authentication service - Business logic for auth operations"""
    
    @staticmethod
    def register(name, email, password, phone_number=None):
        """
        Register new user and send OTP for verification.
        Token is NOT returned until the user verifies their email.
        
        Args:
            name (str): User's full name (required)
            email (str): User's email address (required, unique)
            password (str): User's password (required)
            phone_number (str): User's phone number (optional)
        
        Returns: 
            dict with success status and data
        """
        try:
            # ============================================================
            # VALIDATE BASIC USER INFO
            # ============================================================
            
            if not name or len(name) < 2:
                return {'success': False, 'message': 'Name must be at least 2 characters'}
            
            if not email or '@' not in email:
                return {'success': False, 'message': 'Valid email is required'}
            
            if not password or len(password) < 6:
                return {'success': False, 'message': 'Password must be at least 6 characters'}
            
            if phone_number and len(phone_number) < 7:
                return {'success': False, 'message': 'Phone number must be at least 7 characters'}
            
            # ============================================================
            # CREATE USER
            # ============================================================
            
            user_id, user_message = User.create_user(name, email, password, phone_number)
            
            if user_id is None:
                logger.warning(f"User creation failed: {user_message}")
                return {'success': False, 'message': user_message}
            
            logger.info(f"User created with ID: {user_id}")
            
            # ============================================================
            # CREATE USER PROFILE
            # ============================================================
            
            profile_id, profile_message = UserProfile.create_profile(user_id)
            
            if profile_id is None:
                logger.error(f"Profile creation failed for user {user_id}: {profile_message}")
            else:
                logger.info(f"User profile created with ID: {profile_id}")
            
            # ============================================================
            # GENERATE AND SEND OTP
            # ============================================================
            
            otp_code = generate_otp()
            User.save_otp(user_id, otp_code)
            sent, send_msg = send_otp_email(email, otp_code, name)
            
            if not sent:
                logger.error(f"OTP email failed for user {user_id}: {send_msg}")
                return {
                    'success': False,
                    'message': f'Account created but failed to send OTP: {send_msg}'
                }
            
            logger.info(f"OTP sent to {email} for user {user_id}")
            
            return {
                'success': True,
                'message': 'Registration successful. Please check your email for the OTP to verify your account.',
                'user_id': user_id,
                'email': email
            }
        
        except Exception as e:
            logger.error(f"Register error: {str(e)}")
            return {'success': False, 'message': f'Error during registration: {str(e)}'}
    
    @staticmethod
    def login(email, password):
        """
        Login user with email and password.
        Blocks login if the account is not verified.
        
        Args:
            email (str): User's email address
            password (str): User's password
        
        Returns: 
            dict with success status and data (token, user info)
        """
        try:
            if not email or not password:
                return {'success': False, 'message': 'Email and password are required'}
            
            # Get user by email
            user = User.get_user_by_email(email)
            
            if not user:
                logger.warning(f"Login attempt with non-existent email: {email}")
                return {'success': False, 'message': 'Invalid email or password'}
            
            # Check if account is verified
            if not user.get('is_verified'):
                logger.warning(f"Login attempt by unverified user: {email}")
                return {
                    'success': False,
                    'message': 'Please verify your email first. Check your inbox for the OTP.',
                    'requires_verification': True,
                    'email': email
                }
            
            # Verify password
            if not User.verify_password(user['password'], password):
                logger.warning(f"Login attempt with wrong password for user: {email}")
                return {'success': False, 'message': 'Invalid email or password'}
            
            # Generate token
            token = JWTHandler.generate_token(user['id'])
            
            if token is None:
                logger.error(f"Failed to generate token for user {user['id']}")
                return {'success': False, 'message': 'Failed to generate authentication token'}
            
            logger.info(f"User logged in successfully: {user['id']}")
            
            return {
                'success': True,
                'message': 'Login successful',
                'user_id': user['id'],
                'user_name': user['name'],
                'token': token
            }
        
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            return {'success': False, 'message': f'Error during login: {str(e)}'}
    
    @staticmethod
    def verify_token(token):
        """
        Verify JWT token and return user information
        """
        try:
            if not token:
                return {'success': False, 'message': 'No token provided'}
            
            user_id = JWTHandler.verify_token(token)
            
            if user_id is None:
                logger.warning("Token verification failed - invalid or expired")
                return {'success': False, 'message': 'Invalid or expired token'}
            
            user = User.get_user_by_id(user_id)
            
            if not user:
                logger.warning(f"User not found for token: user_id={user_id}")
                return {'success': False, 'message': 'User not found'}
            
            logger.info(f"Token verified successfully for user: {user_id}")
            
            return {
                'success': True,
                'message': 'Token is valid',
                'user_id': user_id,
                'user_name': user['name']
            }
        
        except Exception as e:
            logger.error(f"Token verification error: {str(e)}")
            return {'success': False, 'message': f'Error verifying token: {str(e)}'}
    @staticmethod
    def forgot_password(email):
        """
        Request password reset - send OTP to user's email
        """
        try:
            if not email or '@' not in email:
                return {'success': False, 'message': 'Valid email is required'}
            
            email = email.strip().lower()
            user = User.get_user_by_email(email)
            
            if not user:
                return {'success': False, 'message': 'No account found with this email address'}
            
            otp_code = generate_otp()
            User.save_otp(user['id'], otp_code)
            
            sent, send_msg = send_password_reset_email(email, otp_code, user['name'])
            if not sent:
                return {'success': False, 'message': send_msg}
                
            return {
                'success': True, 
                'message': 'Password reset code sent to your email'
            }
            
        except Exception as e:
            logger.error(f"Forgot password error: {str(e)}")
            return {'success': False, 'message': f'Error: {str(e)}'}

    @staticmethod
    def reset_password(email, otp_code, new_password):
        """
        Reset user's password using OTP verification
        """
        try:
            if not email or not otp_code or not new_password:
                return {'success': False, 'message': 'Email, code, and new password are required'}
            
            email = email.strip().lower()
            
            # Verify OTP (skip verified check since user is likely already verified)
            valid, msg = User.verify_otp(email, otp_code, check_verified=False)
            if not valid:
                return {'success': False, 'message': msg}
            
            user = User.get_user_by_email(email)
            if not user:
                return {'success': False, 'message': 'User not found'}
                
            # Update password
            success, msg = User.update_password(user['id'], new_password)
            if not success:
                return {'success': False, 'message': msg}
                
            # Clear OTP
            User.clear_otp(user['id'])
            
            return {
                'success': True,
                'message': 'Password reset successfully. You can now login.'
            }
            
        except Exception as e:
            logger.error(f"Reset password error: {str(e)}")
            return {'success': False, 'message': f'Error: {str(e)}'}
