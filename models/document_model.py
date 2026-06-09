"""
MedQuery Ingested Document Model

Maps the 'documents' database table to audit RAG inputs files.
"""

from datetime import datetime
from database.connection import db

class Document(db.Model):
    """
    ORM Model representing records of uploaded clinical files.
    """
    __tablename__ = 'documents'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    filename = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(10), nullable=False) # 'pdf', 'txt', 'csv'
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        """
        Converts the ORM object to a dictionary.
        """
        return {
            'id': self.id,
            'filename': self.filename,
            'file_type': self.file_type,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None
        }
