"""
MedQuery Drug Interaction Model

Maps the 'drug_interactions' catalog table schema.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Index
from database.connection import db

class DrugInteraction(db.Model):
    """
    ORM Model representing drug interaction pairings.
    Includes database level indexes on the query keys.
    """
    __tablename__ = 'drug_interactions'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    drug_a = db.Column(db.String(100), nullable=False, index=True)
    drug_b = db.Column(db.String(100), nullable=False, index=True)
    
    # Severity indicator: 'Low', 'Moderate', 'High'
    severity = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        # Unique constraint to prevent duplicate sets in both directions
        # drug_a must be lexicographically smaller than drug_b in insertions
        db.UniqueConstraint('drug_a', 'drug_b', name='unique_drug_pair'),
    )

    def to_dict(self):
        """
        Converts the ORM object to a Python dictionary.
        """
        return {
            'id': self.id,
            'drug_a': self.drug_a,
            'drug_b': self.drug_b,
            'severity': self.severity,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
