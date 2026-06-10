import pytest
from app import create_app
from database.connection import db
from models.drug_model import DrugInteraction
from services.drug_interaction_service import DrugInteractionService
from rag.drug_checker import DrugChecker

@pytest.fixture(scope='module')
def app():
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'SECRET_KEY': 'test-secret'
    })
    
    with app.app_context():
        db.create_all()
        # Seed test database entries
        interaction = DrugInteraction(
            drug_a="aspirin",
            drug_b="warfarin",
            severity="High",
            description="Increases major bleeding risk."
        )
        db.session.add(interaction)
        db.session.commit()
        
        yield app
        db.session.remove()
        db.drop_all()

def test_drug_interaction_service_lookup(app):
    with app.app_context():
        # Test bidirectional case-insensitive database matching
        res1 = DrugInteractionService.check_interaction("Aspirin", "Warfarin")
        assert res1['found'] is True
        assert res1['severity'] == "High"
        
        res2 = DrugInteractionService.check_interaction("warfarin", "ASPIRIN")
        assert res2['found'] is True
        assert res2['severity'] == "High"

def test_drug_interaction_service_fallback(app):
    with app.app_context():
        # Test fallbacks when database lookup fails or pair is not inside database
        res1 = DrugInteractionService.check_interaction("Ibuprofen", "Paracetamol")
        assert res1['found'] is True
        assert res1['severity'] == "Low"
        
        res2 = DrugInteractionService.check_interaction("Amoxicillin", "Azithromycin")
        assert res2['found'] is False
        assert "No interaction data" in res2['message']

def test_drug_checker_rules_engine(app):
    with app.app_context():
        # Test query text parsing and matching
        report = DrugChecker.analyze_query("I need to take aspirin and warfarin together.")
        assert report['has_warnings'] is True
        # SQLite should be accessed because we imported models and created tables
        # If SQLite tables exist, the database check triggers first:
        assert report['severity'] == "High"
        assert "bleeding" in report['description']
        
        # Test fallback hardcoded scanning
        report2 = DrugChecker.analyze_query("Can I take ibuprofen with lisinopril?")
        assert report2['has_warnings'] is True
        assert report2['severity'] == "Moderate"
        assert "renal" in report2['description']
        
        # Test unrelated queries
        report3 = DrugChecker.analyze_query("Just check my blood sugar levels.")
        assert report3['has_warnings'] is False
        assert report3['severity'] == "none"
