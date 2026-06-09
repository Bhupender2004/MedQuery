"""
MedQuery Chat Routing Controllers

Defines endpoint blueprints for interacting with the AI drug assistant.
"""

from flask import Blueprint, request, jsonify
from services.chat_service import ChatService

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/ask', methods=['POST'])
def ask_question():
    """
    POST /api/chat/ask
    Receives user query, processes it through RAG and drug-checker pipelines.
    
    Payload:
        {
            "query": "Can I take Aspirin with Warfarin?",
            "session_id": "session-1234"
        }
    """
    data = request.get_json() or {}
    query = data.get('query')
    session_id = data.get('session_id')

    if not query:
        return jsonify({'error': 'A non-empty query parameter is required.'}), 400

    try:
        response_payload = ChatService.process_query(query, session_id)
        return jsonify(response_payload), 200
    except Exception as err:
        return jsonify({
            'error': 'An error occurred processing the chat request.',
            'message': str(err)
        }), 500

@chat_bp.route('/history', methods=['GET'])
def get_history():
    """
    GET /api/chat/history?session_id=...
    Retrieves previous logs in this session.
    """
    session_id = request.args.get('session_id')
    try:
        logs = ChatService.get_chat_history(session_id)
        return jsonify(logs), 200
    except Exception as err:
        return jsonify({
            'error': 'An error occurred fetching chat logs.',
            'message': str(err)
        }), 500
