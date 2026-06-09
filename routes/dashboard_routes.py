"""
MedQuery Dashboard & Page View Routing Controllers

Defines template routes to render web pages and analytical stats endpoints.
"""

from flask import Blueprint, render_template, jsonify
from services.dashboard_service import DashboardService

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard', methods=['GET'])
def dashboard_page():
    """
    GET /dashboard
    Renders analytical logs and system statistics dashboards.
    """
    return render_template('dashboard.html')

@dashboard_bp.route('/chat', methods=['GET'])
def chat_page():
    """
    GET /chat
    Renders conversational assistant interface.
    """
    return render_template('chat.html')

@dashboard_bp.route('/upload', methods=['GET'])
def upload_page():
    """
    GET /upload
    Renders document upload deck.
    """
    return render_template('upload.html')

@dashboard_bp.route('/api/dashboard/stats', methods=['GET'])
def get_stats():
    """
    GET /api/dashboard/stats
    Aggregates analytical indicators.
    """
    try:
        metrics = DashboardService.get_metrics()
        return jsonify(metrics), 200
    except Exception as err:
        return jsonify({
            'error': 'An exception occurred compiling dashboard stats.',
            'message': str(err)
        }), 500
