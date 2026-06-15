"""
MedQuery Dashboard Service

Aggregates system database statistics, warnings distribution, and queue lengths.
"""

from datetime import datetime, timedelta
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

            # 1. Weekly Audit Volume (last 7 days grouped by day)
            start_date = datetime.utcnow() - timedelta(days=6)
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
            
            recent_logs_7d = QueryLog.query.filter(QueryLog.created_at >= start_date).all()
            
            daily_counts = {}
            for i in range(7):
                dt = start_date + timedelta(days=i)
                day_label = dt.strftime('%b %d')
                day_str = dt.strftime('%Y-%m-%d')
                daily_counts[day_str] = {'label': day_label, 'count': 0}
                
            for log in recent_logs_7d:
                day_str = log.created_at.strftime('%Y-%m-%d')
                if day_str in daily_counts:
                    daily_counts[day_str]['count'] += 1
                    
            weekly_labels = [val['label'] for val in daily_counts.values()]
            weekly_values = [val['count'] for val in daily_counts.values()]

            # 2. Most Flagged Compounds (top 5 from warning logs)
            drug_counts = {}
            flagged_logs = QueryLog.query.filter_by(has_interaction_warnings=True).all()
            all_interactions = DrugInteraction.query.all()
            
            for log in flagged_logs:
                q_lower = log.user_query.lower()
                for rule in all_interactions:
                    drug_a = rule.drug_a.lower()
                    drug_b = rule.drug_b.lower()
                    if drug_a in q_lower and drug_b in q_lower:
                        drug_counts[rule.drug_a] = drug_counts.get(rule.drug_a, 0) + 1
                        drug_counts[rule.drug_b] = drug_counts.get(rule.drug_b, 0) + 1
            
            sorted_drugs = sorted(drug_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            most_flagged_labels = [item[0] for item in sorted_drugs]
            most_flagged_values = [item[1] for item in sorted_drugs]

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
                'weekly_audit_volume': {
                    'labels': weekly_labels,
                    'values': weekly_values
                },
                'most_flagged_drugs': {
                    'labels': most_flagged_labels,
                    'values': most_flagged_values
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
                'weekly_audit_volume': {
                    'labels': [],
                    'values': []
                },
                'most_flagged_drugs': {
                    'labels': [],
                    'values': []
                },
                'recent_queries': [],
                'status': 'offline_fallback_waiting_migrations'
            }
        
