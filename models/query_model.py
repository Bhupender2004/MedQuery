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
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        """
        Converts the ORM object to a dictionary.
        """
        return {
            'id': self.id,
            'question': self.question,
            'answer': self.answer,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }
