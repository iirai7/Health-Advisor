from app.database import db
import logging

logger = logging.getLogger(__name__)


class MedicalHistory:
    """Model for user_medical_history and user_medical_conditions tables."""

    # ============================================================
    # MEDICAL HISTORY CRUD
    # ============================================================

    @staticmethod
    def get_by_user_id(user_id):
        """
        Fetch the medical history record for a user.

        Returns:
            dict | None: Row as dictionary, or None if not found.
        """
        try:
            cursor = db.get_cursor()
            cursor.execute(
                "SELECT * FROM user_medical_history WHERE user_id = %s",
                (user_id,)
            )
            return cursor.fetchone()
        except Exception as e:
            logger.error(f"Error fetching medical history for user {user_id}: {e}")
            return None

    @staticmethod
    def create(user_id):
        """
        Insert an empty medical history record for a new user.
        Called at the start of the gathering stage.

        Returns:
            tuple: (history_id, message)
        """
        try:
            cursor = db.get_cursor()
            connection = db.get_connection()
            cursor.execute(
                "INSERT INTO user_medical_history (user_id) VALUES (%s)",
                (user_id,)
            )
            connection.commit()
            cursor.execute("SELECT LAST_INSERT_ID() as id")
            result = cursor.fetchone()
            history_id = result['id'] if result else None
            logger.info(f"Medical history record created for user {user_id}: id={history_id}")
            return history_id, "Medical history record created"
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating medical history for user {user_id}: {e}")
            return None, f"Error creating medical history: {e}"

    @staticmethod
    def update(user_id, fields: dict):
        """
        Partial update of a user's medical history.
        Only columns present in `fields` are updated.

        Args:
            user_id (int): Target user.
            fields  (dict): Column -> value pairs to update.

        Returns:
            tuple: (success, message)
        """
        if not fields:
            return False, "No fields provided"

        allowed = {
            'date_of_birth', 'gender', 'blood_type', 'height_cm', 'weight_kg',
            'pcp_name', 'pcp_phone', 'pcp_hospital',
            'surgical_history', 'hospitalization_history',
            'current_medications',
            'drug_allergies', 'food_allergies', 'other_allergies',
            'last_checkup_date', 'last_dental_date', 'last_eye_exam_date',
            'vaccinations_up_to_date',
            'smoking_status', 'alcohol_use', 'exercise_frequency',
            'family_history', 'additional_notes', 'is_complete'
        }
        filtered = {k: v for k, v in fields.items() if k in allowed}
        if not filtered:
            return False, "No valid fields provided"

        try:
            cursor = db.get_cursor()
            connection = db.get_connection()
            set_clause = ", ".join(f"{col} = %s" for col in filtered)
            values = list(filtered.values()) + [user_id]
            cursor.execute(
                f"UPDATE user_medical_history SET {set_clause} WHERE user_id = %s",
                values
            )
            connection.commit()
            logger.info(f"Medical history updated for user {user_id}: {list(filtered.keys())}")
            return True, "Medical history updated"
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating medical history for user {user_id}: {e}")
            return False, f"Error updating medical history: {e}"

    @staticmethod
    def mark_complete(user_id):
        """
        Mark a user's medical history as fully collected.
        Triggers mode-switch to 'diagnosis' in the chatbot service.

        Returns:
            tuple: (success, message)
        """
        return MedicalHistory.update(user_id, {'is_complete': 1})

    @staticmethod
    def is_complete(user_id):
        """
        Check whether the medical history gathering is complete.

        Returns:
            bool
        """
        record = MedicalHistory.get_by_user_id(user_id)
        if not record:
            return False
        return bool(record.get('is_complete'))

    # ============================================================
    # CONDITIONS (many-to-many)
    # ============================================================

    @staticmethod
    def get_all_conditions():
        """
        Fetch all rows from medical_conditions_list.

        Returns:
            list[dict]
        """
        try:
            cursor = db.get_cursor()
            cursor.execute("SELECT id, name_en, name_ar FROM medical_conditions_list ORDER BY id")
            return cursor.fetchall() or []
        except Exception as e:
            logger.error(f"Error fetching conditions list: {e}")
            return []

    @staticmethod
    def get_user_conditions(user_id):
        """
        Fetch conditions checked by a specific user, joined with the master list.

        Returns:
            list[dict]: Each row has condition_id, name_en, name_ar, notes.
        """
        try:
            cursor = db.get_cursor()
            cursor.execute(
                """
                SELECT umc.condition_id, mcl.name_en, mcl.name_ar, umc.notes
                FROM user_medical_conditions umc
                JOIN medical_conditions_list mcl ON mcl.id = umc.condition_id
                WHERE umc.user_id = %s
                ORDER BY mcl.id
                """,
                (user_id,)
            )
            return cursor.fetchall() or []
        except Exception as e:
            logger.error(f"Error fetching conditions for user {user_id}: {e}")
            return []

    @staticmethod
    def set_user_conditions(user_id, condition_ids: list):
        """
        Replace all conditions for a user with the provided list.
        Deletes existing entries then inserts the new ones.

        Args:
            user_id       (int): Target user.
            condition_ids (list[int]): IDs from medical_conditions_list.

        Returns:
            tuple: (success, message)
        """
        try:
            cursor = db.get_cursor()
            connection = db.get_connection()

            # Clear existing selections
            cursor.execute(
                "DELETE FROM user_medical_conditions WHERE user_id = %s",
                (user_id,)
            )

            # Insert new selections
            if condition_ids:
                rows = [(user_id, cid) for cid in condition_ids]
                cursor.executemany(
                    "INSERT INTO user_medical_conditions (user_id, condition_id) VALUES (%s, %s)",
                    rows
                )

            connection.commit()
            logger.info(f"Conditions set for user {user_id}: {condition_ids}")
            return True, "Conditions updated"
        except Exception as e:
            db.rollback()
            logger.error(f"Error setting conditions for user {user_id}: {e}")
            return False, f"Error setting conditions: {e}"
