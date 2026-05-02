"""
app/models/user_profile.py - UPDATED VERSION
UserProfile model with learning style support for quiz feature
Keeps all existing methods + adds new quiz-related methods
"""

from app.database import db
import json
import datetime
import logging

logger = logging.getLogger(__name__)


class UserProfile:
    """User Profile model with quiz support"""
    
    @staticmethod
    def create_profile(user_id):
        """
        Create a new user profile
        Returns: (profile_id, message)
        """
        try:
            cursor = db.get_cursor()
            connection = db.get_connection()
            
            # Insert profile with quiz fields initialized
            cursor.execute("""
                INSERT INTO user_profile 
                (user_id, learning_style, quiz_completed, learning_style_scores, created_at)
                VALUES (%s, NULL, FALSE, NULL, %s)
            """, (user_id, datetime.datetime.now()))
            
            connection.commit()
            
            # Get the newly created profile ID
            cursor.execute("SELECT LAST_INSERT_ID() as id")
            result = cursor.fetchone()
            profile_id = result['id'] if result else None
            
            logger.info(f"Profile created successfully: {profile_id}")
            return profile_id, "Profile created successfully"
        
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating profile: {str(e)}")
            return None, f"Error creating profile: {str(e)}"
    
    @staticmethod
    def get_profile_by_user(user_id):
        """
        Get user profile by user_id
        Returns: profile dict or None
        """
        try:
            cursor = db.get_cursor()
            cursor.execute("""
                SELECT 
                    id, user_id, profile_picture, bio, phone_number,
                    learning_style, learning_style_scores, quiz_completed, quiz_completed_at
                FROM user_profile 
                WHERE user_id = %s
            """, (user_id,))
            
            profile = cursor.fetchone()
            
            # Parse JSON if present
            if profile and profile.get('learning_style_scores'):
                profile['learning_style_scores'] = json.loads(profile['learning_style_scores'])
            
            return profile
        
        except Exception as e:
            logger.error(f"Error getting profile: {str(e)}")
            return None
    
    @staticmethod
    def update_profile(user_id, **kwargs):
        """
        Update user profile (bio, phone_number)
        Returns: (success, message)
        """
        try:
            cursor = db.get_cursor()
            connection = db.get_connection()
            
            # Build dynamic update query
            allowed_fields = ['bio', 'phone_number']
            updates = {k: v for k, v in kwargs.items() if k in allowed_fields and v is not None}
            
            if not updates:
                return False, "No valid fields to update"
            
            set_clause = ", ".join([f"{k} = %s" for k in updates.keys()])
            values = list(updates.values()) + [user_id]
            
            query = f"UPDATE user_profile SET {set_clause}, updated_at = NOW() WHERE user_id = %s"
            cursor.execute(query, values)
            
            connection.commit()
            
            logger.info(f"Profile updated successfully for user: {user_id}")
            return True, "Profile updated successfully"
        
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating profile: {str(e)}")
            return False, f"Error updating profile: {str(e)}"
    
    
    # ============================================================
    # NEW QUIZ-RELATED METHODS
    # ============================================================
    
    @staticmethod
    def update_learning_style(user_id, learning_style, learning_style_scores):
        """
        Update user's learning style after quiz completion
        
        Args:
            user_id: User ID
            learning_style: String like 'Auditory', 'Visual', 'Reading/Writing', 'Kinesthetic', or 'Mixed'
            learning_style_scores: Dict with scores for each style
                                  Example: {'Auditory': 8, 'Reading/Writing': 4, 'Visual': 3, 'Kinesthetic': 1}
        
        Returns:
            tuple: (success, message)
        """
        try:
            cursor = db.get_cursor()
            connection = db.get_connection()
            
            # Validate learning style
            valid_styles = ['Auditory', 'Reading/Writing', 'Visual', 'Kinesthetic', 'Mixed']
            if learning_style not in valid_styles:
                return False, f"Invalid learning style. Must be one of: {valid_styles}"
            
            # Convert dict to JSON string if needed
            if isinstance(learning_style_scores, dict):
                scores_json = json.dumps(learning_style_scores)
            else:
                scores_json = learning_style_scores
            
            cursor.execute("""
                UPDATE user_profile 
                SET learning_style = %s, 
                    learning_style_scores = %s,
                    quiz_completed = TRUE,
                    quiz_completed_at = NOW()
                WHERE user_id = %s
            """, (learning_style, scores_json, user_id))
            
            connection.commit()
            
            logger.info(f"Learning style updated for user_id={user_id}: {learning_style}")
            return True, f"Learning style updated to {learning_style}"
        
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating learning style: {str(e)}")
            return False, f"Error updating learning style: {str(e)}"
    
    @staticmethod
    def get_learning_style(user_id):
        """
        Get user's learning style
        
        Args:
            user_id: User ID
        
        Returns:
            dict: {
                'learning_style': 'Auditory' / 'Visual' / 'Reading/Writing' / 'Kinesthetic' / 'Mixed' / None,
                'scores': {...},
                'is_completed': True/False,
                'completed_at': timestamp or None
            }
        """
        try:
            cursor = db.get_cursor()
            cursor.execute("""
                SELECT learning_style, learning_style_scores, quiz_completed, quiz_completed_at
                FROM user_profile 
                WHERE user_id = %s
            """, (user_id,))
            
            profile = cursor.fetchone()
            
            if not profile:
                return {
                    'learning_style': None,
                    'scores': None,
                    'is_completed': False,
                    'completed_at': None
                }
            
            scores = None
            if profile['learning_style_scores']:
                scores = json.loads(profile['learning_style_scores'])
            
            return {
                'learning_style': profile['learning_style'],
                'scores': scores,
                'is_completed': profile['quiz_completed'],
                'completed_at': profile['quiz_completed_at']
            }
        
        except Exception as e:
            logger.error(f"Error retrieving learning style: {str(e)}")
            return {
                'learning_style': None,
                'scores': None,
                'is_completed': False,
                'completed_at': None
            }
    
    @staticmethod
    def reset_quiz(user_id):
        """
        Reset quiz completion status and learning style (for retaking)
        
        Args:
            user_id: User ID
        
        Returns:
            tuple: (success, message)
        """
        try:
            cursor = db.get_cursor()
            connection = db.get_connection()
            
            cursor.execute("""
                UPDATE user_profile 
                SET learning_style = NULL, 
                    learning_style_scores = NULL,
                    quiz_completed = FALSE,
                    quiz_completed_at = NULL
                WHERE user_id = %s
            """, (user_id,))
            
            connection.commit()
            
            logger.info(f"Quiz reset for user_id={user_id}")
            return True, "Quiz reset successfully"
        
        except Exception as e:
            db.rollback()
            logger.error(f"Error resetting quiz: {str(e)}")
            return False, f"Error resetting quiz: {str(e)}"
    
    @staticmethod
    def is_quiz_completed(user_id):
        """
        Check if user has completed the learning style quiz
        
        Args:
            user_id: User ID
        
        Returns:
            bool: True if quiz completed, False otherwise
        """
        try:
            cursor = db.get_cursor()
            cursor.execute("""
                SELECT quiz_completed FROM user_profile WHERE user_id = %s
            """, (user_id,))
            
            result = cursor.fetchone()
            return result['quiz_completed'] if result else False
        
        except Exception as e:
            logger.error(f"Error checking quiz completion: {str(e)}")
            return False
