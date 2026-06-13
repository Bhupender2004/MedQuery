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
    
    # Eagerly preload heavy resources in a background thread to prevent first-query latency
    if not debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        import threading
        from rag.embeddings import EmbeddingService
        from rag.retrieval import RetrievalService
        
        def preload_resources():
            print("MedQuery Preloader: Eagerly preloading SentenceTransformer and ChromaDB...")
            try:
                # Eagerly initialize embedding model
                EmbeddingService.get_model()
                # Eagerly initialize ChromaDB client and collection
                RetrievalService.get_collection()
                print("MedQuery Preloader: Eager preloading completed successfully.")
            except Exception as preload_err:
                print(f"MedQuery Preloader Warning: Eager loading encountered an error: {preload_err}")

        preload_thread = threading.Thread(target=preload_resources, daemon=True)
        preload_thread.start()

    print(f"Starting MedQuery Server at http://{host}:{port}/ (Debug: {debug})")
    app.run(host=host, port=port, debug=debug)
