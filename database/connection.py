"""
MedQuery Database Connection Manager

Loads credentials from environment, configures SQLAlchemy core engine and SessionLocal,
declares the database model Base, and exports connectivity validation checks.
"""

import os
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# Ensure environment variables are loaded
load_dotenv()

# Read configurations from .env
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "medquery")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")

# Construct the standard MySQL Connection string
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# 1. Create Core SQLAlchemy Engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,      # Checks connection health before queries
    pool_recycle=3600,       # Recycles connections every hour
    echo=False               # Set to True for SQL query debugging
)

# 2. Configure Scoped Session Factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 3. Base class for declarative models
Base = declarative_base()

# 4. Flask-SQLAlchemy Global Instantiation for Web Application integration
db = SQLAlchemy()

def init_db(app):
    """
    Integrates database session bindings with the Flask app context.
    """
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    
    with app.app_context():
        try:
            # Create MySQL tables using Flask context as backup
            db.create_all()
            print("MedQuery: Flask-SQLAlchemy database tables verified.")
        except Exception as err:
            print(f"MedQuery: DB tables registration skipped/deferred: {err}")

def test_db_connection():
    """
    Connection testing utility to verify database connectivity.
    
    Returns:
        bool: True if connection was successful, False otherwise.
    """
    print(f"Testing connection to MySQL Database: '{DB_NAME}' at {DB_HOST}:{DB_PORT}...")
    try:
        # Acquire a connection and run simple SELECT 1
        with engine.connect() as conn:
            from sqlalchemy import text
            conn.execute(text("SELECT 1"))
        print("Database connection test: SUCCESS")
        return True
    except Exception as err:
        print(f"Database connection test: FAILED\nReason: {err}")
        return False
