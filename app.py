"""
MedQuery Flask Application Factory

Initializes extensions, loads environmental configuration, creates necessary directories,
and registers blueprints for routes.
"""

import os
from flask import Flask, render_template

def create_app(test_config=None):
    """
    Application Factory for MedQuery.
    
    Args:
        test_config (dict, optional): Configuration dictionary for testing overrides.
    
    Returns:
        Flask: Instantiated and configured Flask application.
    """
    app = Flask(__name__, instance_relative_config=True)

    # 1. Configuration Loading
    if test_config is not None:
        app.config.from_mapping(test_config)
    else:
        # Load from our system settings
        from config.settings import get_settings
        settings = get_settings()
        # Bind setting attributes directly to flask config
        app.config.from_object(settings)

    # 2. Directory Scaffolding Checks
    # Ensure that folder hierarchies for uploads and vector stores exist locally
    os.makedirs(app.config.get('UPLOAD_FOLDER', 'uploads'), exist_ok=True)
    os.makedirs(app.config.get('CHROMA_PERSIST_DIR', 'chroma_db'), exist_ok=True)

    # 3. Database Initialization
    from database.connection import init_db
    init_db(app)

    # 4. Blueprint Registration
    # Blueprints decouple route controllers logically
    from routes.chat_routes import chat_bp
    from routes.upload_routes import upload_bp
    from routes.dashboard_routes import dashboard_bp

    app.register_blueprint(chat_bp, url_prefix='/api/chat')
    app.register_blueprint(upload_bp, url_prefix='/api/upload')
    app.register_blueprint(dashboard_bp)

    # 5. Root Application Routes
    @app.route('/')
    def index():
        """
        Renders the home/landing portal page of MedQuery.
        """
        return render_template('index.html')

    # 6. Global Error Handlers
    @app.errorhandler(404)
    def not_found_error(error):
        """
        Fallback renderer for route misses.
        """
        return render_template('index.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        """
        Fallback renderer for unhandled server exceptions.
        """
        return "Internal Server Error. Please contact administrator.", 500

    return app
