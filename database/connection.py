"""
MedQuery Database Connection and Initializer

Configures Flask-SQLAlchemy context instances and exposes database utility hooks.
"""

from flask_sqlalchemy import SQLAlchemy

# Instantiate the SQLAlchemy extension globally.
# Will be bound to Flask app within init_db.
db = SQLAlchemy()

def init_db(app):
    """
    Binds the SQLAlchemy extension to the Flask application.
    Attempts to execute schema migrations or automatic table creations.
    
    Args:
        app (Flask): The target Flask application instance.
    """
    db.init_app(app)
    
    # Trigger database check inside app context
    with app.app_context():
        try:
            # Import models here to ensure they are registered with SQLAlchemy metadata
            import models
            
            # Create tables if they do not exist.
            # Handles exceptions gracefully if MySQL is not online during initial scaffold setup.
            db.create_all()
            print("Successfully checked/initialized MySQL database tables.")
        except Exception as err:
            print(f"Database Initialization warning (App runs anyway): {err}")
            print("Please check your DATABASE_URL in .env once MySQL is running.")
