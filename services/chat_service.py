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
    def process_query(query, session_id=None):
        """
        Executes complete RAG query transaction.
        1. Checks for structured drug-drug interaction alerts in text.
        2. Retrieves semantic match chunks from ChromaDB.
        3. Formulates a prompt and calls Google Gemini API.
        4. Logs transaction parameters to MySQL database.
        
        Args:
            query (str): User query sentence.
            session_id (str, optional): Chat session ID.
            
        Returns:
            dict: Structured response object.
        """
        # 1. Structural Interaction check
        drug_alert = DrugChecker.analyze_query(query)
        has_warnings = drug_alert.get('has_warnings', False)
        severity = drug_alert.get('severity', 'none')

        # 2. Vector DB contexts retrieve
        chunks = RetrievalService.retrieve(query)

        # 3. LLM Orchestrator reasoning
        ai_response = LLMService.generate_response(query, chunks, drug_alert)

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
            'citations': chunks
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
