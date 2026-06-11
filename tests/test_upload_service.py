import os
import pytest
from unittest.mock import patch, MagicMock
from io import BytesIO
from werkzeug.datastructures import FileStorage
from app import create_app
from database.connection import db
from services.upload_service import UploadService
from models.document_model import Document

@pytest.fixture(scope='module')
def app():
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'SECRET_KEY': 'test-secret',
        'UPLOAD_FOLDER': './test_uploads'
    })
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()
        
    # Clean up test uploads directory if created
    if os.path.exists('./test_uploads'):
        import shutil
        shutil.rmtree('./test_uploads')

def test_allowed_file():
    assert UploadService.allowed_file("test.pdf") is True
    assert UploadService.allowed_file("test.txt") is True
    assert UploadService.allowed_file("test.csv") is True
    assert UploadService.allowed_file("test.png") is False
    assert UploadService.allowed_file("test.docx") is False
    assert UploadService.allowed_file("test") is False

def test_get_document_status_missing(app):
    with app.app_context():
        res = UploadService.get_document_status(9999)
        assert 'error' in res
        assert 'was not identified' in res['error']

def test_handle_upload_flow(app):
    with app.app_context():
        file_data = BytesIO(b"Clinical safety guidelines context. Aspirin and Warfarin have high risk.")
        file = FileStorage(
            stream=file_data,
            filename="clinical_guidelines.txt",
            content_type="text/plain"
        )
        
        # We need to mock IngestionService.ingest_file to avoid executing actual embedding generation
        # in the upload unit tests (to isolate the test).
        from unittest.mock import patch
        with patch('services.upload_service.IngestionService.ingest_file') as mock_ingest:
            result = UploadService.handle_upload(file)
            
            assert result['filename'] == "clinical_guidelines.txt"
            assert result['status'] == "processing"
            assert result['document_id'] is not None
            
            # Verify file exists on disk
            filepath = os.path.join('./test_uploads', "clinical_guidelines.txt")
            assert os.path.exists(filepath)
            
            # Verify database log entry was created
            doc = Document.query.get(result['document_id'])
            assert doc is not None
            assert doc.filename == "clinical_guidelines.txt"
            assert doc.status == "processing"
            
            # Verify status fetching
            status_info = UploadService.get_document_status(doc.id)
            assert status_info['filename'] == "clinical_guidelines.txt"
            assert status_info['status'] == "processing"
            
            mock_ingest.assert_called_once_with(filepath, doc.id)

def test_handle_upload_async_trigger(app):
    with app.app_context():
        from flask import current_app
        original_testing = current_app.config.get('TESTING')
        current_app.config['TESTING'] = False
        
        try:
            file_data = BytesIO(b"Some text info.")
            file = FileStorage(
                stream=file_data,
                filename="async_test.txt",
                content_type="text/plain"
            )
            
            # Mock threading.Thread and ingest_file
            with patch('threading.Thread') as mock_thread_class, \
                 patch('services.upload_service.IngestionService.ingest_file') as mock_ingest:
                
                mock_thread_instance = MagicMock()
                mock_thread_class.return_value = mock_thread_instance
                
                result = UploadService.handle_upload(file)
                
                # Verify that IngestionService.ingest_file WAS NOT called synchronously
                mock_ingest.assert_not_called()
                
                # Verify that Thread was created and started
                mock_thread_class.assert_called_once()
                mock_thread_instance.start.assert_called_once()
                
                # Clean up local file created during test
                filepath = os.path.join('./test_uploads', "async_test.txt")
                if os.path.exists(filepath):
                    os.remove(filepath)
        finally:
            current_app.config['TESTING'] = original_testing

