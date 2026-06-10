"""
MedQuery Drug Interaction Checking Rules Engine

Performs structural checks for known interacting chemical combinations against SQL models or offline rules.
"""

class DrugChecker:
    """
    Scans incoming sentences for drug references and pulls interaction severity levels.
    """

    @staticmethod
    def analyze_query(query):
        """
        Scans strings for pharmaceutical tokens.
        Checks database rules or falls back to pre-defined medical checks if offline.
        
        Args:
            query (str): Input text from chat.
            
        Returns:
            dict: Interaction report containing severity and descriptions.
        """
        query_clean = query.lower()

        # 1. Attempt database scan using SQLAlchemy models
        try:
            from models.drug_model import DrugInteraction
            # Retrieve available interactions catalogue
            rules = DrugInteraction.query.all()
            for rule in rules:
                drug_a = rule.drug_a.lower()
                drug_b = rule.drug_b.lower()
                # If both drugs are referenced in the sentence, trigger warning
                if drug_a in query_clean and drug_b in query_clean:
                    return {
                        'has_warnings': True,
                        'severity': rule.severity,
                        'description': rule.description
                    }
        except Exception as db_err:
            print(f"Warning: Local SQL drug catalog checks bypassed: {db_err}")

        # 2. Hardcoded fallback checks for standard demonstration pairs:
        # Standard: Aspirin + Warfarin
        if 'aspirin' in query_clean and 'warfarin' in query_clean:
            return {
                'has_warnings': True,
                'severity': 'major',
                'description': "Concomitant use of Aspirin and Warfarin increases bleeding risks due to "
                               "additive antiplatelet and anticoagulant pharmacological actions."
            }

        # Standard: Ibuprofen + Lisinopril
        if 'ibuprofen' in query_clean and 'lisinopril' in query_clean:
            return {
                'has_warnings': True,
                'severity': 'moderate',
                'description': "NSAIDs like Ibuprofen reduce renal perfusion and may diminish the therapeutic "
                               "anti-hypertensive efficacy of ACE inhibitors such as Lisinopril."
            }

        return {
            'has_warnings': False,
            'severity': 'none',
            'description': ''
        }
