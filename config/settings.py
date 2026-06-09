"""
MedQuery Application Settings Configuration

Exposes structural settings using environment variables and sets sensible fallbacks.
"""

import os

class Config:
    """
    Settings Schema mapping environment variables to Flask app configuration keys.
    """
    # Flask application security key
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-this-in-production')

    # Flask Environments
    ENV = os.getenv('FLASK_ENV', 'development')
    DEBUG = os.getenv('FLASK_DEBUG', '1') == '1'

    # Database Configuration (MySQL Connection via SQLAlchemy)
    # Default points to a local mysql database named 'medquery_db'
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL', 
        'mysql+pymysql://root:password@localhost:3306/medquery_db'
    )
    # Turn off overhead modifications tracker
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # AI / LLM Configurations
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
    EMBEDDING_MODEL_NAME = os.getenv('EMBEDDING_MODEL_NAME', 'all-MiniLM-L6-v2')

    # Storage Paths
    CHROMA_PERSIST_DIR = os.getenv('CHROMA_PERSIST_DIR', 'chroma_db')
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')

    # Upload limitations (16MB by default)
    try:
        MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 16777216))
    except ValueError:
        MAX_CONTENT_LENGTH = 16777216  # 16MB fallback

def get_settings():
    """
    Factory function to retrieve settings instance configuration.
    """
    return Config
