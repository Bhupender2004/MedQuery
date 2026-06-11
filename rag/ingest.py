"""
MedQuery RAG Document Ingest Service

Handles reading file streams, text chunk extractions, vector bindings, and DB status indicators.
"""

import os
from database.connection import db
from models.document_model import Document
from rag.chunking import Chunker
from rag.embeddings import EmbeddingService

class IngestionService:
    """
    Service parsing text formats, partitioning segments, calling embeddings loaders,
    and persisting results to ChromaDB collections.
    """

    @staticmethod
    def ingest_file(filepath, document_id):
        """
        Parses target file and loads vector embeddings in ChromaDB.
        Updates document state in MySQL database to completed or failed.
        
        Args:
            filepath (str): Absolute file location on disk.
            document_id (int): SQL database row key of target document records.
        """
        try:
            # 1. Text extraction step
            # Handle standard TXT / CSV. PDFs require libraries like PyPDF2, mock fallback text extraction
            filename = os.path.basename(filepath)
            file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
            
            chunks = []
            if file_ext in ['txt', 'csv']:
                raw_text = ""
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as file_stream:
                    raw_text = file_stream.read()
                chunks = Chunker.split_text(raw_text, chunk_size=800, chunk_overlap=150)
            elif file_ext == 'pdf':
                import pypdf
                reader = pypdf.PdfReader(filepath)
                for page_idx, page in enumerate(reader.pages):
                    page_text = page.extract_text()
                    if not page_text or not page_text.strip():
                        continue
                    page_chunks = Chunker.split_text(page_text, chunk_size=800, chunk_overlap=150)
                    for chunk in page_chunks:
                        chunk['page'] = page_idx + 1
                        chunks.append(chunk)
            else:
                raise ValueError(f"Extension format '.{file_ext}' is not supported in processing.")

            if not chunks:
                print(f"Warning: No valid segments extracted from {filename}.")
                chunks = [{"text": "Empty file context", "page": 1}]

            # Attach source context metadata to segments
            for index, chunk in enumerate(chunks):
                chunk['metadata'] = {
                    'source': filename,
                    'page': chunk.get('page', 1),
                    'chunk_index': index,
                    'document_id': document_id
                }

            # 3. Vector calculation
            texts_list = [c['text'] for c in chunks]
            embeddings_list = EmbeddingService.embed_texts(texts_list)

            # 4. ChromaDB insertion
            try:
                import chromadb
                from flask import current_app
                persist_dir = current_app.config.get('CHROMA_PERSIST_DIR', 'chroma_db')
                
                chroma_client = chromadb.PersistentClient(path=persist_dir)
                collection = chroma_client.get_or_create_collection(name="medical_documents")
                
                ids = [f"doc_{document_id}_chunk_{i}" for i in range(len(chunks))]
                metadatas = [chunk['metadata'] for chunk in chunks]
                
                collection.add(
                    ids=ids,
                    embeddings=embeddings_list,
                    metadatas=metadatas,
                    documents=texts_list
                )
                print(f"ChromaDB: Successfully inserted {len(chunks)} text chunks for: {filename}.")
            except Exception as chroma_err:
                print(f"Warning: Failed to save vectors to ChromaDB: {chroma_err}")

            # 5. Database Status update
            doc_record = Document.query.get(document_id)
            if doc_record:
                doc_record.status = 'completed'
                db.session.commit()
                print(f"Ingestion succeeded for document ID {document_id}.")

        except Exception as err:
            print(f"Error inside ingestion pipeline: {err}")
            # Mark database record state as failed to release locks
            try:
                doc_record = Document.query.get(document_id)
                if doc_record:
                    doc_record.status = 'failed'
                    db.session.commit()
            except Exception as db_err:
                print(f"Could not transition database state: {db_err}")
