import pytest
from app import create_app
from database.connection import db, SessionLocal
from models.document_model import Document
from models.drug_model import DrugInteraction
from models.query_model import QueryLog

@pytest.fixture(scope='module')
def app():
    # Setup test app config
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'SECRET_KEY': 'test-secret'
    })
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def session(app):
    # Retrieve clean SQLAlchemy session
    connection = db.engine.connect()
    transaction = connection.begin()
    
    # Create local sessionmaker
    from sqlalchemy.orm import scoped_session, sessionmaker
    session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=connection))
    
    original_session = db.session
    db.session = session
    
    yield session
    
    transaction.rollback()
    connection.close()
    session.remove()
    db.session = original_session

def test_document_crud(session):
    doc = Document(
        filename="safety_guideline.pdf",
        filepath="/tmp/safety_guideline.pdf",
        file_size=1024,
        status="pending"
    )
    session.add(doc)
    session.commit()
    
    # Read
    saved_doc = session.query(Document).filter_by(filename="safety_guideline.pdf").first()
    assert saved_doc is not None
    assert saved_doc.file_size == 1024
    assert saved_doc.status == "pending"
    
    # Update
    saved_doc.status = "completed"
    session.commit()
    
    updated_doc = session.query(Document).filter_by(id=saved_doc.id).first()
    assert updated_doc.status == "completed"
    
    # Delete
    session.delete(updated_doc)
    session.commit()
    
    deleted_doc = session.query(Document).filter_by(id=saved_doc.id).first()
    assert deleted_doc is None

def test_drug_interaction_crud(session):
    interaction = DrugInteraction(
        drug_a="aspirin",
        drug_b="warfarin",
        severity="High",
        description="Increased bleeding risk"
    )
    session.add(interaction)
    session.commit()
    
    saved = session.query(DrugInteraction).filter_by(drug_a="aspirin").first()
    assert saved is not None
    assert saved.drug_b == "warfarin"
    assert saved.severity == "High"
    
    # Convert to dict
    data = saved.to_dict()
    assert data['drug_a'] == "aspirin"
    assert data['severity'] == "High"

def test_query_log_crud(session):
    query = QueryLog(
        session_id="session-xyz",
        user_query="Can I mix ibuprofen and aspirin?",
        ai_response="Consult clinical notes.",
        citations="[]",
        has_interaction_warnings=False,
        severity_level="none"
    )
    session.add(query)
    session.commit()
    
    saved = session.query(QueryLog).filter_by(session_id="session-xyz").first()
    assert saved is not None
    assert saved.user_query == "Can I mix ibuprofen and aspirin?"
    assert saved.has_interaction_warnings is False
