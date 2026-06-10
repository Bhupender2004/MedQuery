import pytest
import json
from io import BytesIO
from app import create_app
from database.connection import db
from unittest.mock import patch

@pytest.fixture(scope='module')
def client():
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'SECRET_KEY': 'test-secret',
        'UPLOAD_FOLDER': './test_uploads_api'
    })
    
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.session.remove()
        db.drop_all()
        
    if os.path.exists('./test_uploads_api'):
        import shutil, os
        shutil.rmtree('./test_uploads_api')

import os

def test_page_renders(client):
    # Test HTML view routes
    r1 = client.get('/')
    assert r1.status_code == 200
    assert b"AI-Powered" in r1.data
    
    r2 = client.get('/chat')
    assert r2.status_code == 200
    assert b"Verify Interaction" in r2.data
    
    r3 = client.get('/upload')
    assert r3.status_code == 200
    assert b"Ingest Medical Guidelines" in r3.data
    
    r4 = client.get('/dashboard')
    assert r4.status_code == 200
    assert b"Analytics Console" in r4.data

def test_chat_endpoint_validation(client):
    # 1. Missing query
    res = client.post('/api/chat/ask', json={})
    assert res.status_code == 400
    assert b"query parameter is required" in res.data
    
    # 2. Correct query with warnings
    with patch('services.chat_service.LLMService.generate_response') as mock_llm:
        mock_llm.return_value = "Avoid taking Warfarin with Aspirin."
        
        response = client.post('/api/chat/ask', json={
            "query": "Aspirin and Warfarin combination?",
            "session_id": "session-1"
        })
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['has_warnings'] is True
        assert data['severity'] == "High"
        assert "Aspirin" in data['response'] or "Warfarin" in data['response']

def test_chat_history_endpoint(client):
    res = client.get('/api/chat/history?session_id=session-1')
    assert res.status_code == 200
    data = json.loads(res.data)
    assert isinstance(data, list)

def test_upload_endpoint_validation(client):
    # 1. Missing file key
    res = client.post('/api/upload')
    assert res.status_code == 400
    assert b"No file attachment" in res.data
    
    # 2. Disallowed extension
    data_disallowed = {
        'file': (BytesIO(b"file content"), 'test.png')
    }
    res = client.post('/api/upload', data=data_disallowed, content_type='multipart/form-data')
    assert res.status_code == 400
    assert b"Unsupported extension" in res.data

    # 3. Allowed extension
    data_allowed = {
        'file': (BytesIO(b"File safety info on Metformin and Alcohol"), 'clinical_safety.txt')
    }
    with patch('services.upload_service.IngestionService.ingest_file') as mock_ingest:
        res = client.post('/api/upload', data=data_allowed, content_type='multipart/form-data')
        assert res.status_code == 202
        resp_json = json.loads(res.data)
        assert resp_json['filename'] == "clinical_safety.txt"
        assert resp_json['status'] == "processing"

def test_dashboard_stats_endpoint(client):
    res = client.get('/api/dashboard/stats')
    assert res.status_code == 200
    data = json.loads(res.data)
    assert 'total_documents' in data
    assert 'total_queries' in data
    assert 'total_warnings' in data
    assert 'severity_distribution' in data
