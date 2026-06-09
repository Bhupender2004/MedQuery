"""
MedQuery Drug Interaction Database Model

Defines catalog relational tables for known drug interactions, severity classes, and recommendations.
"""

from datetime import datetime
from database.connection import db

class DrugInteraction(db.Model):
    """
    Relational catalog representing known drug-drug interactions.
    Serves as an authoritative local lookup dataset.
    """
    __tablename__ = 'drug_interactions'

    id = db.Column(db.Integer, primary_key=True)
    drug_a = db.Column(db.String(100), nullable=False)
    drug_b = db.Column(db.String(100), nullable=False)
    
    # Severity indicators: 'minor', 'moderate', 'major'
    severity = db.Column(db.String(50), nullable=False)
    
    mechanism = db.Column(db.Text, nullable=True)
    recommendation = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        """
        Serializes interaction metadata schemas.
        """
        return {
            'id': self.id,
            'drug_a': self.drug_a,
            'drug_b': self.drug_b,
            'severity': self.severity,
            'mechanism': self.mechanism,
            'recommendation': self.recommendation,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
