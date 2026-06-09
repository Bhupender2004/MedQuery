"""
MedQuery Document Upload Routing Controllers

Handles document transfers, validation rules, and vector indexing triggers.
"""

from flask import Blueprint, request, jsonify
from services.upload_service import UploadService

upload_bp = Blueprint('upload', __name__)

@upload_bp.route('', methods=['POST'])
def upload_file():
    """
    POST /api/upload
    Receives file payload (PDF/TXT), registers document in database, 
    and schedules text digestion.
    """
    if 'file' not in request.files:
        return jsonify({'error': 'No file attachment identified in request payload.'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Selected filename must not be blank.'}), 400

    try:
        result = UploadService.handle_upload(file)
        # 202 Accepted signifies background ingestion trigger
        return jsonify(result), 202
    except ValueError as val_err:
        return jsonify({'error': str(val_err)}), 400
    except Exception as err:
        return jsonify({
            'error': 'An internal exception occurred handling uploaded content.',
            'message': str(err)
        }), 500

@upload_bp.route('/status/<int:document_id>', methods=['GET'])
def get_status(document_id):
    """
    GET /api/upload/status/<id>
    Checks document processing queue status.
    """
    try:
        status_info = UploadService.get_document_status(document_id)
        return jsonify(status_info), 200
    except Exception as err:
        return jsonify({
            'error': 'An error occurred fetching index state.',
            'message': str(err)
        }), 500
