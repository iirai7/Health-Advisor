from flask import Blueprint, request, jsonify
from app.services.chatbot_service import ChatbotService
import logging

chatbot_bp = Blueprint('chatbot', __name__, url_prefix='/api/chatbot')
logger = logging.getLogger(__name__)


# ============================================================
# ENDPOINT 1: START OR RESUME SESSION
# ============================================================

@chatbot_bp.route('/start', methods=['POST'])
def start_session():
    """
    Start or resume a chatbot session
    
    Expected JSON: {
        "user_id": 1,
        "language": "en"  // optional, default is "en"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
            
        user_id = data.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': 'user_id is required'}), 400
            
        language = data.get('language', 'en').lower()
        
        result = ChatbotService.start_session(user_id=user_id, language=language)
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Chatbot start session error: {str(e)}")
        return jsonify({'success': False, 'message': f'Error starting session: {str(e)}'}), 500


# ============================================================
# ENDPOINT 2: SEND MESSAGE
# ============================================================

@chatbot_bp.route('/message', methods=['POST'])
def send_message():
    """
    Process a user message and return the assistant reply
    
    Expected JSON: {
        "user_id": 1,
        "session_id": 12,
        "message": "I have a headache"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
            
        user_id = data.get('user_id')
        session_id = data.get('session_id')
        user_message = data.get('message')
        
        if not user_id or not session_id or not user_message:
            return jsonify({'success': False, 'message': 'user_id, session_id, and message are required'}), 400
            
        result = ChatbotService.send_message(user_id=user_id, session_id=session_id, user_text=user_message)
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Chatbot send message error: {str(e)}")
        return jsonify({'success': False, 'message': f'Error sending message: {str(e)}'}), 500


# ============================================================
# ENDPOINT 3: RESET SESSION
# ============================================================

@chatbot_bp.route('/reset', methods=['POST'])
def reset_session():
    """
    Archive the current session and open a fresh one.
    
    Expected JSON: {
        "user_id": 1,
        "session_id": 12,
        "language": "en"  // optional
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
            
        user_id = data.get('user_id')
        session_id = data.get('session_id')
        language = data.get('language', 'en').lower()
        
        if not user_id or not session_id:
            return jsonify({'success': False, 'message': 'user_id and session_id are required'}), 400
            
        result = ChatbotService.reset_session(user_id=user_id, session_id=session_id, language=language)
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Chatbot reset session error: {str(e)}")
        return jsonify({'success': False, 'message': f'Error resetting session: {str(e)}'}), 500


# ============================================================
# ENDPOINT 4: GET HISTORY
# ============================================================

@chatbot_bp.route('/history/<int:user_id>', methods=['GET'])
def get_history(user_id):
    """
    Return all sessions and messages for a user
    """
    try:
        result = ChatbotService.get_history(user_id=user_id)
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Chatbot get history error: {str(e)}")
        return jsonify({'success': False, 'message': f'Error getting history: {str(e)}'}), 500
