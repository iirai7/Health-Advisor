from app.models.medical_history import MedicalHistory
from app.models.chatbot_session import ChatbotSession
from app.utils.stage_definitions import MedicalStageDefinitions
from app.services import medical_ai
import logging

logger = logging.getLogger(__name__)

EMERGENCY_NUMBER = medical_ai.EMERGENCY_NUMBER
_stages = MedicalStageDefinitions


class ChatbotService:
    """Orchestration layer — routes messages through gathering and diagnosis stages."""

    # ============================================================
    # SESSION INIT
    # ============================================================

    @staticmethod
    def start_session(user_id: int, language: str = 'en') -> dict:
        """
        Start or resume a chatbot session.

        - Resumes an existing active session if one exists.
        - Otherwise creates a new gathering or diagnosis session.

        Returns:
            dict: { success, session_id, stage, current_stage, language, message, first_question }
        """
        try:
            existing = ChatbotSession.get_active_session(user_id)
            if existing:
                # Determine the next question to re-show the user
                first_q = ChatbotService._get_current_question(
                    existing['stage'],
                    existing.get('current_stage', 1),
                    existing['language']
                )
                return {
                    'success': True,
                    'session_id': existing['id'],
                    'stage': existing['stage'],
                    'current_stage': existing.get('current_stage', 1),
                    'language': existing['language'],
                    'message': 'Session resumed',
                    'first_question': first_q,
                }

            # Ensure a history record exists
            if not MedicalHistory.get_by_user_id(user_id):
                MedicalHistory.create(user_id)

            if MedicalHistory.is_complete(user_id):
                stage = 'diagnosis'
                current_stage = 1
            else:
                stage = 'gathering'
                current_stage = 1

            session_id, msg = ChatbotSession.create_session(
                user_id, stage=stage, language=language, current_stage=current_stage
            )
            if not session_id:
                return {'success': False, 'message': msg}

            first_q = ChatbotService._get_current_question(stage, current_stage, language)

            # Persist the opening question as an assistant message
            ChatbotSession.add_message(session_id, user_id, 'assistant', first_q)

            logger.info(f"Session started for user {user_id}: id={session_id}, stage={stage}")
            return {
                'success': True,
                'session_id': session_id,
                'stage': stage,
                'current_stage': current_stage,
                'language': language,
                'message': 'Session started',
                'first_question': first_q,
            }

        except Exception as e:
            logger.error(f"Error starting session for user {user_id}: {e}")
            return {'success': False, 'message': str(e)}

    # ============================================================
    # SEND MESSAGE
    # ============================================================

    @staticmethod
    def send_message(user_id: int, session_id: int, user_text: str) -> dict:
        """
        Process a user message and return the assistant reply.

        Flow:
          - Emergency pre-screen (always)
          - Gathering mode: extract stage value → save → advance or re-ask
          - Diagnosis mode stages 1-5: acknowledge → advance
          - Diagnosis mode stage 6: full assessment → reset to stage 1

        Returns:
            dict: { success, reply, is_emergency, stage, current_stage }
        """
        try:
            session = ChatbotSession.get_active_session(user_id)
            if not session or session['id'] != session_id:
                return {'success': False, 'message': 'Session not found or inactive'}

            stage = session['stage']
            current_stage = session.get('current_stage', 1)
            language = medical_ai._detect_language(user_text, fallback=session['language']) if user_text.strip() else session['language']

            # --- Emergency pre-screen ---
            if medical_ai.quick_emergency_check(user_text):
                emergency_reply = ChatbotService._emergency_reply(language)
                ChatbotSession.add_message(session_id, user_id, 'user', user_text, is_emergency=False)
                ChatbotSession.add_message(session_id, user_id, 'assistant', emergency_reply, is_emergency=True)
                return {
                    'success': True,
                    'reply': emergency_reply,
                    'is_emergency': True,
                    'stage': stage,
                    'current_stage': current_stage,
                }

            # Save user message
            ChatbotSession.add_message(session_id, user_id, 'user', user_text)

            # ---- GATHERING MODE ----
            if stage == 'gathering':
                return ChatbotService._handle_gathering(
                    user_id, session_id, current_stage, language, user_text
                )

            # ---- DIAGNOSIS MODE ----
            return ChatbotService._handle_diagnosis(
                user_id, session_id, current_stage, language, user_text
            )

        except Exception as e:
            logger.error(f"Error processing message for user {user_id}: {e}")
            return {'success': False, 'message': str(e)}

    # ============================================================
    # RESET SESSION
    # ============================================================

    @staticmethod
    def reset_session(user_id: int, session_id: int, language: str = 'en') -> dict:
        """Archive current session and open a fresh one."""
        try:
            ChatbotSession.close_session(session_id)
            if MedicalHistory.is_complete(user_id):
                stage, current_stage = 'diagnosis', 1
            else:
                stage, current_stage = 'gathering', 1

            new_session_id, msg = ChatbotSession.create_session(
                user_id, stage=stage, language=language, current_stage=current_stage
            )
            if not new_session_id:
                return {'success': False, 'message': msg}

            first_q = ChatbotService._get_current_question(stage, current_stage, language)
            ChatbotSession.add_message(new_session_id, user_id, 'assistant', first_q)

            logger.info(f"Session reset for user {user_id}: new session id={new_session_id}")
            return {
                'success': True,
                'session_id': new_session_id,
                'stage': stage,
                'current_stage': current_stage,
                'message': 'Session reset successfully',
                'first_question': first_q,
            }
        except Exception as e:
            logger.error(f"Error resetting session for user {user_id}: {e}")
            return {'success': False, 'message': str(e)}

    # ============================================================
    # HISTORY
    # ============================================================

    @staticmethod
    def get_history(user_id: int) -> dict:
        try:
            history = ChatbotSession.get_full_history(user_id)
            return {'success': True, 'history': history}
        except Exception as e:
            logger.error(f"Error fetching history for user {user_id}: {e}")
            return {'success': False, 'message': str(e)}

    # ============================================================
    # INTERNAL — GATHERING HANDLER
    # ============================================================

    @staticmethod
    def _handle_gathering(user_id, session_id, current_stage, language, user_text):
        result = medical_ai.run_gathering_stage(current_stage, user_text, language)

        ack = result.get('bot_response', '')
        is_valid = result.get('is_valid', False)

        if not is_valid:
            # Re-ask with clarification
            if ack:
                ChatbotSession.add_message(session_id, user_id, 'assistant', ack)
            return {
                'success': True,
                'reply': ack,
                'is_emergency': False,
                'stage': 'gathering',
                'current_stage': current_stage,
            }

        # Save extracted fields to medical history
        extracted = result.get('extracted', {})
        if extracted:
            # Remove null values so we don't overwrite existing data with None
            clean = {k: v for k, v in extracted.items() if v is not None}
            if clean:
                MedicalHistory.update(user_id, clean)

        next_stage = current_stage + 1

        if _stages.is_gathering_complete(next_stage):
            # All 9 stages done → mark history complete and switch to diagnosis
            MedicalHistory.mark_complete(user_id)
            ChatbotSession.update_stage(session_id, 'diagnosis')
            ChatbotSession.update_current_stage(session_id, 1)

            transition = ChatbotService._transition_message(language)
            first_diag_q = _stages.get_diagnosis_question(1, language)
            reply = f"{ack}\n\n{transition}\n\n{first_diag_q}".strip()

            ChatbotSession.add_message(session_id, user_id, 'assistant', reply)
            return {
                'success': True,
                'reply': reply,
                'is_emergency': False,
                'stage': 'diagnosis',
                'current_stage': 1,
            }

        # Advance to next gathering stage
        ChatbotSession.update_current_stage(session_id, next_stage)
        next_q = _stages.get_gathering_question(next_stage, language)
        reply = f"{ack}\n\n{next_q}".strip() if ack else next_q

        ChatbotSession.add_message(session_id, user_id, 'assistant', reply)
        return {
            'success': True,
            'reply': reply,
            'is_emergency': False,
            'stage': 'gathering',
            'current_stage': next_stage,
        }

    # ============================================================
    # INTERNAL — DIAGNOSIS HANDLER
    # ============================================================

    @staticmethod
    def _handle_diagnosis(user_id, session_id, current_stage, language, user_text):
        total = _stages.TOTAL_DIAGNOSIS_STAGES

        # --- Stages 1–4: acknowledge and advance ---
        if current_stage < total - 1:
            result = medical_ai.run_diagnosis_stage(
                stage_num=current_stage,
                user_message=user_text,
                language=language,
            )
            ack = result.get('bot_response', '')
            next_stage = current_stage + 1
            ChatbotSession.update_current_stage(session_id, next_stage)

            next_q = _stages.get_diagnosis_question(next_stage, language) or ''
            reply = f"{ack}\n\n{next_q}".strip() if next_q else ack

            ChatbotSession.add_message(session_id, user_id, 'assistant', reply)
            return {
                'success': True,
                'reply': reply,
                'is_emergency': False,
                'stage': 'diagnosis',
                'current_stage': next_stage,
            }

        # --- Stage 6: generate assessment ---
        # Build symptom context from the last 10 messages in this session
        recent = ChatbotSession.get_recent_messages(session_id, limit=12)
        symptom_context = "\n".join(
            f"[{m['role'].upper()}]: {m['content']}" for m in recent
        )

        medical_history = MedicalHistory.get_by_user_id(user_id) or {}
        conditions = MedicalHistory.get_user_conditions(user_id)

        result = medical_ai.run_diagnosis_stage(
            stage_num=current_stage,
            user_message=user_text,
            language=language,
            symptom_context=symptom_context,
            medical_history=medical_history,
            conditions=conditions,
        )

        # Format the structured assessment into a clean, readable report
        sections = []
        
        # Check for individual fields from the new structured prompt
        field_labels = {
            'summary': ('📋 الملخص', '📋 Summary'),
            'possible_causes': ('🔍 الأسباب المحتملة', '🔍 Possible Causes'),
            'next_steps': ('✅ الخطوات التالية', '✅ Next Steps')
        }
        
        lang_idx = 1 if language == 'en' else 0
        
        for field, labels in field_labels.items():
            val = result.get(field)
            if val:
                sections.append(f"**{labels[lang_idx]}**\n{val}")
        
        # Fallback to bot_response if it exists
        if not sections:
            reply = result.get('bot_response', '') or ''
            if not isinstance(reply, str):
                reply = str(reply)
        else:
            reply = "\n\n".join(sections)
        is_emergency = result.get('is_emergency', False)

        if is_emergency:
            reply += f"\n\n{ChatbotService._emergency_reply(language)}"

        # Append a prompt to start a new consultation
        new_consult_prompt = (
            "هل تعاني من أعراض أخرى تريد مناقشتها؟"
            if language == 'ar'
            else "Do you have any other symptoms you would like to discuss?"
        )
        reply += f"\n\n{new_consult_prompt}"

        ChatbotSession.add_message(session_id, user_id, 'assistant', reply, is_emergency=is_emergency)

        # Reset diagnosis back to stage 6 to stay in assessment mode for follow-ups
        ChatbotSession.update_current_stage(session_id, 6)

        return {
            'success': True,
            'reply': reply,
            'is_emergency': is_emergency,
            'stage': 'diagnosis',
            'current_stage': 1,
        }

    # ============================================================
    # INTERNAL — HELPERS
    # ============================================================

    @staticmethod
    def _get_current_question(stage: str, current_stage: int, language: str) -> str:
        if stage == 'gathering':
            return _stages.get_gathering_question(current_stage, language)
        return _stages.get_diagnosis_question(current_stage, language) or ''

    @staticmethod
    def _emergency_reply(language: str) -> str:
        if language == 'ar':
            return (
                f"⚠️ **طوارئ طبية**: تشير أعراضك إلى حالة طارئة محتملة. "
                f"يُرجى الاتصال فوراً بالإسعاف على الرقم **{EMERGENCY_NUMBER}** "
                f"أو التوجه إلى أقرب غرفة طوارئ."
            )
        return (
            f"⚠️ **Medical Emergency**: Your symptoms may indicate a serious emergency. "
            f"Please call ambulance services immediately at **{EMERGENCY_NUMBER}** "
            f"or go to the nearest emergency room."
        )

    @staticmethod
    def _transition_message(language: str) -> str:
        if language == 'ar':
            return "✅ تم حفظ سجلك الطبي بنجاح. يمكنك الآن وصف أعراضك الحالية وسأساعدك في تقييمها."
        return "✅ Your medical history has been saved. You can now describe your current symptoms and I will help assess them."
