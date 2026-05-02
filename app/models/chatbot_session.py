from app.database import db
import logging

logger = logging.getLogger(__name__)


class ChatbotSession:
    """Model for chatbot_sessions and chat_messages tables."""

    # ============================================================
    # SESSION MANAGEMENT
    # ============================================================

    @staticmethod
    def get_active_session(user_id):
        """Fetch the currently active session for a user. Returns dict | None."""
        try:
            cursor = db.get_cursor()
            cursor.execute(
                """
                SELECT * FROM chatbot_sessions
                WHERE user_id = %s AND is_active = 1
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (user_id,)
            )
            return cursor.fetchone()
        except Exception as e:
            logger.error(f"Error fetching active session for user {user_id}: {e}")
            return None

    @staticmethod
    def create_session(user_id, stage='gathering', language='en', current_stage=1):
        """
        Create a new chatbot session.

        Args:
            user_id       (int): Target user.
            stage         (str): 'gathering' or 'diagnosis'.
            language      (str): 'en' or 'ar'.
            current_stage (int): Numeric sub-stage (1-9 for gathering, 1-6 for diagnosis).

        Returns:
            tuple: (session_id, message)
        """
        try:
            cursor = db.get_cursor()
            connection = db.get_connection()
            cursor.execute(
                """
                INSERT INTO chatbot_sessions (user_id, stage, language, current_stage, is_active)
                VALUES (%s, %s, %s, %s, 1)
                """,
                (user_id, stage, language, current_stage)
            )
            connection.commit()
            cursor.execute("SELECT LAST_INSERT_ID() as id")
            result = cursor.fetchone()
            session_id = result['id'] if result else None
            logger.info(f"Session created for user {user_id}: id={session_id}, stage={stage}, current_stage={current_stage}")
            return session_id, "Session created"
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating session for user {user_id}: {e}")
            return None, f"Error creating session: {e}"

    @staticmethod
    def update_stage(session_id, stage):
        """Update the stage enum ('gathering' / 'diagnosis') of a session."""
        try:
            cursor = db.get_cursor()
            connection = db.get_connection()
            cursor.execute(
                "UPDATE chatbot_sessions SET stage = %s WHERE id = %s",
                (stage, session_id)
            )
            connection.commit()
            logger.info(f"Session {session_id} stage updated to '{stage}'")
            return True, "Stage updated"
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating stage for session {session_id}: {e}")
            return False, f"Error updating stage: {e}"

    @staticmethod
    def update_current_stage(session_id, current_stage: int):
        """Update the numeric sub-stage of a session."""
        try:
            cursor = db.get_cursor()
            connection = db.get_connection()
            cursor.execute(
                "UPDATE chatbot_sessions SET current_stage = %s WHERE id = %s",
                (current_stage, session_id)
            )
            connection.commit()
            logger.info(f"Session {session_id} current_stage updated to {current_stage}")
            return True, "Current stage updated"
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating current_stage for session {session_id}: {e}")
            return False, f"Error updating current_stage: {e}"

    @staticmethod
    def update_language(session_id, language):
        """Update the language preference of a session."""
        try:
            cursor = db.get_cursor()
            connection = db.get_connection()
            cursor.execute(
                "UPDATE chatbot_sessions SET language = %s WHERE id = %s",
                (language, session_id)
            )
            connection.commit()
            return True, "Language updated"
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating language for session {session_id}: {e}")
            return False, f"Error updating language: {e}"

    @staticmethod
    def close_session(session_id):
        """Archive (deactivate) a session."""
        try:
            cursor = db.get_cursor()
            connection = db.get_connection()
            cursor.execute(
                "UPDATE chatbot_sessions SET is_active = 0 WHERE id = %s",
                (session_id,)
            )
            connection.commit()
            logger.info(f"Session {session_id} closed (archived)")
            return True, "Session closed"
        except Exception as e:
            db.rollback()
            logger.error(f"Error closing session {session_id}: {e}")
            return False, f"Error closing session: {e}"

    # ============================================================
    # MESSAGE MANAGEMENT
    # ============================================================

    @staticmethod
    def add_message(session_id, user_id, role, content, is_emergency=False):
        """Persist a single chat message."""
        try:
            cursor = db.get_cursor()
            connection = db.get_connection()
            cursor.execute(
                """
                INSERT INTO chat_messages (session_id, user_id, role, content, is_emergency)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (session_id, user_id, role, content, int(is_emergency))
            )
            connection.commit()
            cursor.execute("SELECT LAST_INSERT_ID() as id")
            result = cursor.fetchone()
            return result['id'] if result else None, "Message saved"
        except Exception as e:
            db.rollback()
            logger.error(f"Error saving message for session {session_id}: {e}")
            return None, f"Error saving message: {e}"

    @staticmethod
    def get_recent_messages(session_id, limit=20):
        """
        Fetch the most recent messages oldest-first (for LLM context building).
        """
        try:
            cursor = db.get_cursor()
            cursor.execute(
                """
                SELECT role, content, is_emergency, created_at
                FROM (
                    SELECT role, content, is_emergency, created_at
                    FROM chat_messages
                    WHERE session_id = %s
                    ORDER BY created_at DESC
                    LIMIT %s
                ) sub
                ORDER BY created_at ASC
                """,
                (session_id, limit)
            )
            return cursor.fetchall() or []
        except Exception as e:
            logger.error(f"Error fetching messages for session {session_id}: {e}")
            return []

    @staticmethod
    def get_full_history(user_id):
        """Fetch all sessions and their messages for a user."""
        try:
            cursor = db.get_cursor()
            cursor.execute(
                """
                SELECT id, stage, current_stage, language, is_active, created_at
                FROM chatbot_sessions
                WHERE user_id = %s
                ORDER BY created_at DESC
                """,
                (user_id,)
            )
            sessions = cursor.fetchall() or []
            result = []
            for session in sessions:
                messages = ChatbotSession.get_recent_messages(session['id'], limit=1000)
                result.append({**session, 'messages': messages})
            return result
        except Exception as e:
            logger.error(f"Error fetching full history for user {user_id}: {e}")
            return []
