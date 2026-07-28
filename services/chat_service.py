"""
MedQuery Chat Service

Coordinates RAG components, drug interaction checker layers, and MySQL logs.
"""

import json
from database.connection import db
from models.query_model import QueryLog
from rag.drug_checker import DrugChecker
from rag.retrieval import RetrievalService
from rag.llm import LLMService

class ChatService:
    """
    Business Logic orchestrating chat querying, retrieval context checks,
    LLM reasoning, and database audits.
    """

    @staticmethod
    def process_query(query, session_id=None, files=None):
        """
        Executes complete RAG query transaction.
        1. Process any attached files/images and ingests them.
        2. Checks for structured drug-drug interaction alerts in text.
        3. Retrieves semantic match chunks from ChromaDB.
        4. Formulates a prompt and calls Google Gemini API.
        5. Logs transaction parameters to MySQL database.
        
        Args:
            query (str): User query sentence.
            session_id (str, optional): Chat session ID.
            files (list, optional): List of attached FileStorage objects.
            
        Returns:
            dict: Structured response object.
        """
        attached_files_info = []
        image_paths = []
        
        if files:
            from services.upload_service import UploadService
            from rag.ingest import IngestionService
            from models.document_model import Document
            for file_item in files:
                if file_item and file_item.filename:
                    try:
                        res = UploadService.handle_upload(file_item, session_id=session_id)
                        doc_id = res.get('document_id')
                        doc_record = Document.query.get(doc_id)
                        if doc_record:
                            # Ingest synchronously so document/image vector chunks are immediately accessible
                            IngestionService.ingest_file(doc_record.filepath, doc_id)
                            ext = doc_record.filename.rsplit('.', 1)[1].lower() if '.' in doc_record.filename else ''
                            if ext in ['png', 'jpg', 'jpeg', 'webp']:
                                image_paths.append(doc_record.filepath)
                            attached_files_info.append({
                                'filename': doc_record.filename,
                                'id': doc_id
                            })
                    except Exception as upload_err:
                        print(f"Warning: Failed to process attached file {file_item.filename}: {upload_err}")

        # Fast-path greeting and help classification (only if no files attached)
        if not files:
            query_clean = query.strip().lower().rstrip('?.!')
            words = query_clean.split()
            
            is_greeting = False
            greeting_keywords = {'hi', 'hello', 'hey', 'greetings', 'howdy', 'hola'}
            if len(words) <= 3 and any(w in greeting_keywords for w in words):
                is_greeting = True
            elif query_clean in {'good morning', 'good afternoon', 'good evening', 'hello there', 'hi there'}:
                is_greeting = True
                
            is_help = False
            help_keywords = {'help', 'info', 'information', 'instructions', 'guide'}
            if len(words) <= 4 and any(w in help_keywords for w in words):
                is_help = True
            elif query_clean in {'who are you', 'what are you', 'what is this', 'what is medquery', 'what do you do', 'how does this work', 'how can you help', 'how to use this'}:
                is_help = True

            if is_greeting or is_help:
                if is_greeting:
                    ai_response = (
                        "### 👋 Hello! I am MedQuery, your AI-powered clinical pharmacy assistant.\n\n"
                        "I can help you analyze drug-drug interactions, query medical references, and review safety guidelines. "
                        "You can ask me questions like:\n"
                        "- *\"Can I take Aspirin with Warfarin?\"*\n"
                        "- *\"Is there an issue with Ibuprofen and Lisinopril?\"*\n"
                        "- *\"What are the side effects of Metformin?\"*\n\n"
                        "Additionally, you can attach prescriptions or medical images directly using the **📎 Attach** button or upload documents in the **Upload Desk**.\n\n"
                        "---\n"
                        "*Disclaimer: Always consult a licensed healthcare professional before making any medical decisions.*"
                    )
                else:
                    ai_response = (
                        "### ℹ️ How to use MedQuery\n\n"
                        "MedQuery is designed to assist healthcare professionals in checking medication safety and analyzing clinical documents:\n\n"
                        "1. **Drug Interactions**: Type two or more drug names (e.g., *\"Warfarin + Aspirin\"*) to check if they have known adverse interactions.\n"
                        "2. **Medical Queries & Attachments**: Ask general pharmacological questions or use the **📎 Attach** button in the chat input to send images or PDFs of prescriptions and lab reports.\n"
                        "3. **Document Analysis**: You can also use the **Upload Desk** to upload larger patient prescriptions or medical guidelines.\n\n"
                        "---\n"
                        "*Disclaimer: MedQuery is an educational and analytical tool. Always verify clinical findings with official medical references.*"
                    )

                # Fast log saving
                try:
                    log_entry = QueryLog(
                        session_id=session_id,
                        user_query=query,
                        ai_response=ai_response,
                        citations=json.dumps([]),
                        has_interaction_warnings=False,
                        severity_level='none'
                    )
                    db.session.add(log_entry)
                    db.session.commit()
                except Exception as db_err:
                    db.session.rollback()
                    print(f"Warning: Failed to save fast-path query log: {db_err}")

                return {
                    'response': ai_response,
                    'has_warnings': False,
                    'severity': 'none',
                    'description': '',
                    'citations': [],
                    'attachments': attached_files_info
                }

        # 1. Structural Interaction check
        drug_alert = DrugChecker.analyze_query(query)
        has_warnings = drug_alert.get('has_warnings', False)
        severity = drug_alert.get('severity', 'none')

        # 2. Vector DB contexts retrieve
        chunks = RetrievalService.retrieve(query, session_id=session_id)

        # 3. LLM Orchestrator reasoning
        ai_response = LLMService.generate_response(query, chunks, drug_alert, image_paths=image_paths)

        # 4. Serialize citations metadata
        citations_data = [
            {
                'source': chunk.get('metadata', {}).get('source', 'Unknown'),
                'page': chunk.get('metadata', {}).get('page', 0),
                'score': chunk.get('score', 0.0)
            }
            for chunk in chunks
        ]

        # Map drug interaction severity ('Low', 'Moderate', 'High') to query log severity_level ('minor', 'moderate', 'major')
        severity_mapping = {
            'Low': 'minor',
            'low': 'minor',
            'Moderate': 'moderate',
            'moderate': 'moderate',
            'High': 'major',
            'high': 'major',
            'major': 'major',
            'minor': 'minor'
        }
        severity_level = severity_mapping.get(severity, 'none')

        # 5. Persistent SQL Logging
        log_entry = QueryLog(
            session_id=session_id,
            user_query=query,
            ai_response=ai_response,
            citations=json.dumps(citations_data),
            has_interaction_warnings=has_warnings,
            severity_level=severity_level
        )

        try:
            db.session.add(log_entry)
            db.session.commit()
        except Exception as db_err:
            db.session.rollback()
            # Log issue and continue gracefully to support offline DB executions
            print(f"Warning: Failed to save query history log: {db_err}")

        return {
            'response': ai_response,
            'has_warnings': has_warnings,
            'severity': severity,
            'description': drug_alert.get('description', ''),
            'citations': chunks,
            'attachments': attached_files_info
        }

    @staticmethod
    def get_chat_history(session_id=None):
        """
        Retrieves logs in ascending chronological order.
        
        Args:
            session_id (str, optional): Filters logs by chat session.
            
        Returns:
            list: List of serialized query log dictionaries.
        """
        try:
            # Query builder
            query_builder = QueryLog.query
            if session_id:
                query_builder = query_builder.filter_by(session_id=session_id)
            
            logs = query_builder.order_by(QueryLog.created_at.asc()).all()
            return [log.to_dict() for log in logs]
        except Exception as db_err:
            print(f"Warning: Failed to retrieve historical logs: {db_err}")
            return []

    @staticmethod
    def get_distinct_sessions():
        """
        Retrieves a list of all distinct sessions, ordered by the latest message time desc.
        """
        try:
            from sqlalchemy import func
            
            # Subquery to find the first message (min ID) for each session
            first_msg_subquery = db.session.query(
                QueryLog.session_id,
                func.min(QueryLog.id).label('min_id'),
                func.max(QueryLog.created_at).label('last_updated')
            ).group_by(QueryLog.session_id).subquery()
            
            # Join QueryLog to get the user_query of the first message
            results = db.session.query(
                QueryLog.session_id,
                QueryLog.user_query,
                first_msg_subquery.c.last_updated
            ).join(
                first_msg_subquery,
                QueryLog.id == first_msg_subquery.c.min_id
            ).order_by(
                first_msg_subquery.c.last_updated.desc()
            ).all()
            
            sessions_list = []
            for session_id, first_query, last_updated in results:
                if not session_id:
                    continue
                # Truncate first query for title
                title = first_query[:30] + "..." if len(first_query) > 30 else first_query
                if session_id == 'demo-session-token':
                    title = "Demo Conversation"
                sessions_list.append({
                    'session_id': session_id,
                    'title': title,
                    'last_updated': last_updated.isoformat() if last_updated else None
                })
            return sessions_list
        except Exception as db_err:
            print(f"Warning: Failed to retrieve distinct sessions: {db_err}")
            return []

    @staticmethod
    def delete_session(session_id):
        """
        Deletes all logged queries, uploaded documents (including physical files),
        and vector chunks from ChromaDB associated with a session ID.
        """
        import os
        try:
            # 1. Delete associated QueryLog records
            QueryLog.query.filter_by(session_id=session_id).delete()

            # 2. Find associated Document records
            from models.document_model import Document
            docs = Document.query.filter_by(session_id=session_id).all()

            # 3. Clean up physical files for each document
            for doc in docs:
                if doc.filepath and os.path.exists(doc.filepath):
                    try:
                        os.remove(doc.filepath)
                        print(f"File removed: {doc.filepath}")
                    except Exception as fs_err:
                        print(f"Warning: Failed to delete file on disk: {fs_err}")
                
                # Delete Document record
                db.session.delete(doc)

            # 4. Clean up ChromaDB collection vectors
            try:
                collection = RetrievalService.get_collection()
                if collection:
                    collection.delete(where={'session_id': session_id})
                    print(f"ChromaDB: Cleared vectors for session: {session_id}")
            except Exception as chroma_err:
                print(f"Warning: Failed to delete session vectors from ChromaDB: {chroma_err}")

            db.session.commit()
            return True
        except Exception as err:
            db.session.rollback()
            print(f"Error deleting session: {err}")
            raise err

    @staticmethod
    def delete_log(log_id):
        """
        Deletes a single QueryLog entry by its ID.
        """
        try:
            log_entry = db.session.get(QueryLog, log_id)
            if log_entry:
                db.session.delete(log_entry)
                db.session.commit()
                return True
            return False
        except Exception as err:
            db.session.rollback()
            print(f"Error deleting log entry {log_id}: {err}")
            raise err

