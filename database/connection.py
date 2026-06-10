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

# 1. Create Core SQLAlchemy Engine with SQLite fallback
def create_app_engine():
    """
    Tries to connect to MySQL. If unreachable, falls back to SQLite.
    """
    mysql_url = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    sqlite_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "medquery.db"))
    sqlite_url = f"sqlite:///{sqlite_path.replace(os.sep, '/')}"
    
    try:
        # Create MySQL engine with a low timeout to prevent blocking startup
        mysql_engine = create_engine(
            mysql_url,
            pool_pre_ping=True,      # Checks connection health before queries
            pool_recycle=3600,       # Recycles connections every hour
            echo=False,
            connect_args={"connect_timeout": 2}
        )
        # Check connection
        with mysql_engine.connect() as conn:
            from sqlalchemy import text
            conn.execute(text("SELECT 1"))
        print(f"Database connection test: SUCCESS (MySQL)")
        return mysql_engine, mysql_url
    except Exception as err:
        print(f"Warning: MySQL connection failed ({err}). Falling back to SQLite.")
        sqlite_engine = create_engine(
            sqlite_url,
            echo=False
        )
        return sqlite_engine, sqlite_url

engine, DATABASE_URL = create_app_engine()

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
            # Create tables using Flask context
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
    print(f"Testing database connection using active engine...")
    try:
        with engine.connect() as conn:
            from sqlalchemy import text
            conn.execute(text("SELECT 1"))
        print("Database connection test: SUCCESS")
        return True
    except Exception as err:
        print(f"Database connection test: FAILED\nReason: {err}")
        return False

