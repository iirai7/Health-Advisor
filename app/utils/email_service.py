from flask_mail import Mail, Message
import random
import string
import logging

logger = logging.getLogger(__name__)

mail = Mail()


def generate_otp(length=6):
    """Generate a random numeric OTP"""
    return ''.join(random.choices(string.digits, k=length))


def send_otp_email(to_email, otp_code, user_name='User'):
    """
    Send OTP verification email
    
    Args:
        to_email (str): Recipient email address
        otp_code (str): The OTP code to send
        user_name (str): Recipient's name for personalization
    
    Returns:
        tuple: (success, message)
    """
    try:
        msg = Message(
            subject='Your Verification Code - Diagnosis App',
            recipients=[to_email]
        )
        msg.html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 500px; margin: auto; padding: 30px; border: 1px solid #e0e0e0; border-radius: 8px;">
            <h2 style="color: #2c3e50;">Hello, {user_name}!</h2>
            <p style="color: #555;">Use the verification code below to complete your registration:</p>
            <div style="background: #f4f4f4; padding: 20px; text-align: center; border-radius: 6px; margin: 20px 0;">
                <h1 style="letter-spacing: 8px; color: #2c3e50; margin: 0;">{otp_code}</h1>
            </div>
            <p style="color: #888; font-size: 13px;">This code expires in <strong>10 minutes</strong>. Do not share it with anyone.</p>
            <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
            <p style="color: #aaa; font-size: 12px;">If you did not request this, please ignore this email.</p>
        </div>
        """
        mail.send(msg)
        logger.info(f"OTP email sent to {to_email}")
        return True, "OTP sent successfully"

    except Exception as e:
        logger.error(f"Failed to send OTP email to {to_email}: {str(e)}")
        return False, f"Failed to send email: {str(e)}"


def send_member_welcome_email(to_email, member_name, parent_name, auto_password, relation):
    """
    Send welcome email to a newly added family member with their login credentials.

    Args:
        to_email (str): Family member's email (their username)
        member_name (str): Family member's name
        parent_name (str): Primary account owner's name
        auto_password (str): Auto-generated password
        relation (str): Relation to primary user

    Returns:
        tuple: (success, message)
    """
    try:
        msg = Message(
            subject='You have been added to a Family Account - Diagnosis App',
            recipients=[to_email]
        )
        msg.html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 500px; margin: auto; padding: 30px; border: 1px solid #e0e0e0; border-radius: 8px;">
            <h2 style="color: #2c3e50;">Hello, {member_name}!</h2>
            <p style="color: #555;">
                <strong>{parent_name}</strong> has added you as a family member
                (<strong>{relation}</strong>) on the <strong>Diagnosis App</strong>.
            </p>
            <p style="color: #555;">Your login credentials are:</p>
            <div style="background: #f4f4f4; padding: 20px; border-radius: 6px; margin: 20px 0;">
                <p style="margin: 5px 0;"><strong>Username (Email):</strong> {to_email}</p>
                <p style="margin: 5px 0;"><strong>Password:</strong> {auto_password}</p>
            </div>
            <p style="color: #e74c3c; font-size: 13px;">
                ⚠️ Please log in and change your password immediately.
                Your username (email) cannot be changed.
            </p>
            <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
            <p style="color: #aaa; font-size: 12px;">If you did not expect this, please contact support.</p>
        </div>
        """
        mail.send(msg)
        logger.info(f"Welcome email sent to family member: {to_email}")
        return True, "Welcome email sent successfully"

    except Exception as e:
        logger.error(f"Failed to send welcome email to {to_email}: {str(e)}")
        return False, f"Failed to send email: {str(e)}"


def send_password_reset_email(to_email, otp_code, user_name='User'):
    """
    Send password reset OTP email
    
    Args:
        to_email (str): Recipient email address
        otp_code (str): The OTP code to send
        user_name (str): Recipient's name for personalization
    
    Returns:
        tuple: (success, message)
    """
    try:
        msg = Message(
            subject='Password Reset Code - Diagnosis App',
            recipients=[to_email]
        )
        msg.html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 500px; margin: auto; padding: 30px; border: 1px solid #e0e0e0; border-radius: 8px;">
            <h2 style="color: #2c3e50;">Hello, {user_name}!</h2>
            <p style="color: #555;">You requested to reset your password. Use the code below to proceed:</p>
            <div style="background: #f4f4f4; padding: 20px; text-align: center; border-radius: 6px; margin: 20px 0;">
                <h1 style="letter-spacing: 8px; color: #2c3e50; margin: 0;">{otp_code}</h1>
            </div>
            <p style="color: #888; font-size: 13px;">This code expires in <strong>10 minutes</strong>. If you did not request this, please ignore this email.</p>
            <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
            <p style="color: #aaa; font-size: 12px;">Diagnosis App Security Team</p>
        </div>
        """
        mail.send(msg)
        logger.info(f"Password reset email sent to {to_email}")
        return True, "Reset code sent successfully"

    except Exception as e:
        logger.error(f"Failed to send password reset email to {to_email}: {str(e)}")
        return False, f"Failed to send email: {str(e)}"
