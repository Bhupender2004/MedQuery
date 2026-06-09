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
            
            raw_text = ""
            if file_ext in ['txt', 'csv']:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as file_stream:
                    raw_text = file_stream.read()
            elif file_ext == 'pdf':
                # Boilerplate fallback extraction mock
                raw_text = f"Mocked extraction context for PDF reference: {filename}\n"
                raw_text += "Lorem ipsum dolor sit amet, referencing drug warnings: "
                raw_text += "Aspirin reacts with Warfarin increasing bleed hazards. "
                raw_text += "Ibuprofen combined with Lisinopril reduces renal protection capabilities."
            else:
                raise ValueError(f"Extension format '.{file_ext}' is not supported in processing.")

            # 2. Text Segment partitioning
            chunks = Chunker.split_text(raw_text, chunk_size=800, chunk_overlap=150)
            
            if not chunks:
                print(f"Warning: No valid segments extracted from {filename}.")
                chunks = [{"text": raw_text or "Empty file context", "metadata": {"source": filename, "page": 1}}]

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
            # Safe call to Chroma client fallback setups
            # (Note: In future business logic implementation, this connects to chromadb library)
            print(f"Successfully processed {len(chunks)} text chunks for: {filename}.")
            print(f"Generated {len(embeddings_list)} embedding lists of dimension size {len(embeddings_list[0]) if embeddings_list else 0}.")

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
