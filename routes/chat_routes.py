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

@chat_bp.route('/sessions', methods=['GET'])
def get_sessions():
    """
    GET /api/chat/sessions
    Retrieves a list of all distinct sessions with titles and timestamps.
    """
    try:
        sessions = ChatService.get_distinct_sessions()
        return jsonify(sessions), 200
    except Exception as err:
        return jsonify({
            'error': 'An error occurred fetching distinct sessions.',
            'message': str(err)
        }), 500

@chat_bp.route('/session/<session_id>', methods=['DELETE'])
def delete_session(session_id):
    """
    DELETE /api/chat/session/<session_id>
    Cleans up all logs, documents, files, and vector chunks for a session.
    """
    if not session_id:
        return jsonify({'error': 'A session_id parameter is required.'}), 400

    try:
        ChatService.delete_session(session_id)
        return jsonify({'message': f'Session {session_id} successfully deleted.'}), 200
    except Exception as err:
        return jsonify({
            'error': 'An error occurred deleting the session.',
            'message': str(err)
        }), 500

@chat_bp.route('/log/<int:log_id>', methods=['DELETE'])
def delete_log(log_id):
    """
    DELETE /api/chat/log/<log_id>
    Deletes a single QueryLog entry.
    """
    try:
        success = ChatService.delete_log(log_id)
        if success:
            return jsonify({'message': f'Log entry {log_id} successfully deleted.'}), 200
        else:
            return jsonify({'error': f'Log entry {log_id} not found.'}), 404
    except Exception as err:
        return jsonify({
            'error': 'An error occurred deleting the log entry.',
            'message': str(err)
        }), 500

