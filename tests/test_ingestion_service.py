import os
import pytest
from unittest.mock import patch, MagicMock
from app import create_app
from database.connection import db
from models.document_model import Document
from rag.ingest import IngestionService

@pytest.fixture(scope='module')
def app():
    # Setup test app config
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'SECRET_KEY': 'test-secret',
        'UPLOAD_FOLDER': './test_uploads_ingest',
        'CHROMA_PERSIST_DIR': './test_chroma_ingest'
    })
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def clean_db(app):
    with app.app_context():
        # Clear previous docs
        Document.query.delete()
        db.session.commit()
        yield db.session

def test_ingest_txt_file(app, clean_db):
    with app.app_context():
        # Create a temp txt file
        os.makedirs('./test_uploads_ingest', exist_ok=True)
        txt_path = './test_uploads_ingest/test_doc.txt'
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write("Line one text context. Line two text context.")

        doc = Document(
            filename="test_doc.txt",
            filepath=txt_path,
            file_size=100,
            status="processing"
        )
        clean_db.add(doc)
        clean_db.commit()

        # Mock ChromaDB client and Embedding service
        with patch('chromadb.PersistentClient') as mock_chroma, \
             patch('rag.embeddings.EmbeddingService.embed_texts', return_value=[[0.1]*384]):
            
            IngestionService.ingest_file(txt_path, doc.id)

            # Assert status updated to completed
            updated_doc = Document.query.get(doc.id)
            assert updated_doc.status == "completed"

        if os.path.exists(txt_path):
            os.remove(txt_path)

def test_ingest_pdf_file(app, clean_db):
    with app.app_context():
        # Create a dummy pdf file on disk (does not need to be a valid PDF since we mock PdfReader)
        os.makedirs('./test_uploads_ingest', exist_ok=True)
        pdf_path = './test_uploads_ingest/test_doc.pdf'
        with open(pdf_path, 'wb') as f:
            f.write(b"%PDF-1.4 mock content")

        doc = Document(
            filename="test_doc.pdf",
            filepath=pdf_path,
            file_size=100,
            status="processing"
        )
        clean_db.add(doc)
        clean_db.commit()

        # Mock pypdf, ChromaDB client and Embedding service
        mock_reader = MagicMock()
        mock_page_1 = MagicMock()
        mock_page_1.extract_text.return_value = "Page 1 context of medication. Aspirin reacts with Warfarin."
        mock_page_2 = MagicMock()
        mock_page_2.extract_text.return_value = "Page 2 context of medication. Ibuprofen reacts with Lisinopril."
        mock_reader.pages = [mock_page_1, mock_page_2]

        with patch('pypdf.PdfReader', return_value=mock_reader) as mock_pdf_reader, \
             patch('chromadb.PersistentClient') as mock_chroma, \
             patch('rag.embeddings.EmbeddingService.embed_texts', return_value=[[0.1]*384, [0.2]*384]):
            
            # Use spy to track chunk collections added to chromadb
            mock_collection = MagicMock()
            mock_chroma.return_value.get_or_create_collection.return_value = mock_collection
            
            IngestionService.ingest_file(pdf_path, doc.id)

            # Assert status updated to completed
            updated_doc = Document.query.get(doc.id)
            assert updated_doc.status == "completed"

            # Assert pypdf Reader was called
            mock_pdf_reader.assert_called_once_with(pdf_path)
            
            # Check arguments of collection.add
            mock_collection.add.assert_called_once()
            called_kwargs = mock_collection.add.call_args[1]
            
            # Verify metadatas had correct page numbers
            metadatas = called_kwargs['metadatas']
            assert len(metadatas) == 2
            assert metadatas[0]['page'] == 1
            assert metadatas[1]['page'] == 2
            assert metadatas[0]['document_id'] == doc.id

        if os.path.exists(pdf_path):
            os.remove(pdf_path)
