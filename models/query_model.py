"""
MedQuery Chat Log Query Model

Maps the 'queries' database table schema.
"""

from datetime import datetime
from database.connection import db

class QueryLog(db.Model):
    """
    ORM Model recording prompts, generation summaries, and analytical timestamps.
    """
    __tablename__ = 'queries'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    session_id = db.Column(db.String(100), nullable=True)
    user_query = db.Column(db.Text, nullable=False)
    ai_response = db.Column(db.Text, nullable=False)
    
    # JSON-encoded string mapping document chunks referenced by retrieval
    citations = db.Column(db.Text, nullable=True)
    
    # Flag to easily query hazard metrics
    has_interaction_warnings = db.Column(db.Boolean, default=False, nullable=False)
    
    # Hazard categorization: 'none', 'minor', 'moderate', 'major'
    severity_level = db.Column(db.String(50), default='none', nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        """
        Converts the ORM object to a dictionary.
        """
        return {
            'id': self.id,
            'session_id': self.session_id,
            'user_query': self.user_query,
            'ai_response': self.ai_response,
            'citations': self.citations,
            'has_interaction_warnings': self.has_interaction_warnings,
            'severity_level': self.severity_level,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
