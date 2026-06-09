"""
MedQuery Document Database Model

Maps stored medical references and ingestion tracking within MySQL.
"""

from datetime import datetime
from database.connection import db

class Document(db.Model):
    """
    Represents an uploaded reference document file in the system.
    Used for audit trails and ingestion states mapping in the RAG pipeline.
    """
    __tablename__ = 'documents'

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(512), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    
    # Status flags: 'pending', 'processing', 'completed', 'failed'
    status = db.Column(db.String(50), default='pending', nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        """
        Serializes the document instance to a JSON-compatible dictionary.
        """
        return {
            'id': self.id,
            'filename': self.filename,
            'filepath': self.filepath,
            'file_size': self.file_size,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
