"""
MedQuery Upload Service

Validates incoming medical documents, saves them to disk, and triggers RAG ingestion.
"""

import os
from werkzeug.utils import secure_filename
from database.connection import db
from models.document_model import Document
from rag.ingest import IngestionService

ALLOWED_EXTENSIONS = {'pdf', 'txt', 'csv', 'png', 'jpg', 'jpeg', 'webp'}

class UploadService:
    """
    Business logic handling uploaded files, auditing record insertions,
    and launching ChromaDB vector segment integrations.
    """

    @staticmethod
    def allowed_file(filename):
        """
        Validates file extensions.
        """
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

    @staticmethod
    def handle_upload(file, session_id=None):
        """
        Performs file validation, directory saves, and triggers the RAG ingest system.
        
        Args:
            file (FileStorage): Flask file storage package.
            session_id (str, optional): Association key for session-specific document scoping.
            
        Returns:
            dict: Metadata properties showing success details.
        """
        if not file or not file.filename:
            raise ValueError("No valid file payload received.")

        if not UploadService.allowed_file(file.filename):
            raise ValueError("Unsupported extension. Allowed extensions are: PDF, TXT, CSV, PNG, JPG, JPEG, WEBP.")

        filename = secure_filename(file.filename)
        
        # Fetch configurations from Flask App context
        from flask import current_app
        upload_dir = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save file to uploads folder
        filepath = os.path.join(upload_dir, filename)
        file.save(filepath)

        # Retrieve file properties
        file_size = os.path.getsize(filepath)

        # Log document entry
        doc_entry = Document(
            session_id=session_id,
            filename=filename,
            filepath=filepath,
            file_size=file_size,
            status='processing'
        )

        try:
            db.session.add(doc_entry)
            db.session.commit()
            
            # Trigger RAG ingestion pipeline execution asynchronously
            from flask import current_app
            if current_app.config.get('TESTING'):
                # Synchronous run under testing conditions to prevent race conditions and test flakiness
                IngestionService.ingest_file(filepath, doc_entry.id)
            else:
                import threading
                app = current_app._get_current_object()
                
                def async_ingest_task(app_context, path, doc_id):
                    with app_context.app_context():
                        try:
                            IngestionService.ingest_file(path, doc_id)
                        except Exception as async_err:
                            print(f"Background ingestion task failed for document {doc_id}: {async_err}")

                threading.Thread(
                    target=async_ingest_task,
                    args=(app, filepath, doc_entry.id),
                    daemon=True
                ).start()
            
        except Exception as err:
            db.session.rollback()
            # If storage registration failed, try deleting temporary file
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                except OSError:
                    pass
            raise RuntimeError(f"Failed to record file details: {err}")

        return {
            'message': 'File uploaded and RAG ingestion sequence initiated successfully.',
            'document_id': doc_entry.id,
            'filename': filename,
            'status': doc_entry.status
        }

    @staticmethod
    def get_document_status(document_id):
        """
        Retrieves status mappings for individual documents in queue.
        """
        try:
            doc_record = Document.query.get(document_id)
            if not doc_record:
                return {'error': f"Document with ID {document_id} was not identified."}
            return doc_record.to_dict()
        except Exception as err:
            print(f"Warning: Failed to fetch document status: {err}")
            return {'error': str(err)}
