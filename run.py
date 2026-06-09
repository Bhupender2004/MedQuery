"""
MedQuery Entrypoint

Loads environment configurations and bootstraps the Flask application server.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

from app import create_app

app = create_app()

if __name__ == '__main__':
    host = os.getenv('FLASK_HOST', '127.0.0.1')
    try:
        port = int(os.getenv('FLASK_PORT', 5000))
    except ValueError:
        port = 5000
    
    # Enable debugging during development by default
    debug = os.getenv('FLASK_DEBUG', '1') == '1'
    
    print(f"Starting MedQuery Server at http://{host}:{port}/ (Debug: {debug})")
    app.run(host=host, port=port, debug=debug)
