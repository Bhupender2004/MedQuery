"""
MedQuery Dashboard Service

Aggregates system database statistics, warnings distribution, and queue lengths.
"""

from models.document_model import Document
from models.query_model import QueryLog
from models.drug_model import DrugInteraction

class DashboardService:
    """
    Consolidates SQL queries for frontend dashboard cards and analytical visualization blocks.
    """

    @staticmethod
    def get_metrics():
        """
        Gathers count metrics from database models.
        Returns a mock fallback payload if database tables are uninitialized/offline.
        
        Returns:
            dict: Summary metrics.
        """
        try:
            total_docs = Document.query.count()
            total_queries = QueryLog.query.count()
            total_warnings = QueryLog.query.filter_by(has_interaction_warnings=True).count()
            rules_count = DrugInteraction.query.count()

            # Retrieve breakdown count by severities
            minor_warnings = QueryLog.query.filter_by(severity_level='minor').count()
            moderate_warnings = QueryLog.query.filter_by(severity_level='moderate').count()
            major_warnings = QueryLog.query.filter_by(severity_level='major').count()

            # Fetch recent queries for the dashboard logs activity feed
            recent_logs = QueryLog.query.order_by(QueryLog.created_at.desc()).limit(5).all()
            recent_queries_dict = [log.to_dict() for log in recent_logs]

            return {
                'total_documents': total_docs,
                'total_queries': total_queries,
                'total_warnings': total_warnings,
                'rules_count': rules_count,
                'severity_distribution': {
                    'minor': minor_warnings,
                    'moderate': moderate_warnings,
                    'major': major_warnings
                },
                'recent_queries': recent_queries_dict,
                'status': 'active'
            }
        except Exception as db_err:
            print(f"Warning: Dashboard statistics compilation bypassed: {db_err}")
            # Return template layout to prevent server error screens prior to DB migrations
            return {
                'total_documents': 0,
                'total_queries': 0,
                'total_warnings': 0,
                'rules_count': 0,
                'severity_distribution': {
                    'minor': 0,
                    'moderate': 0,
                    'major': 0
                },
                'recent_queries': [],
                'status': 'offline_fallback_waiting_migrations'
            }
        
