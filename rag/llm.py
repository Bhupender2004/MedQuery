"""
MedQuery RAG LLM Integration Service

Interfaces with Google Gemini APIs to formulate answers, including simulated offline backups.
"""

import os

class LLMService:
    """
    Constructs prompts incorporating semantic snippets and drug database alerts.
    Invokes Google's generative models or returns mock answers if API credentials are not set.
    """

    @staticmethod
    def generate_response(query, contexts, drug_alert):
        """
        Formulates clinical replies using the Gemini model.
        
        Args:
            query (str): User query text.
            contexts (list): Retrieval chunks.
            drug_alert (dict): Active drug safety checks.
            
        Returns:
            str: Markdown formatted response.
        """
        api_key = os.getenv('GEMINI_API_KEY', '')

        # Construct reference context prompt blocks
        reference_text = ""
        for chunk in contexts:
            source = chunk.get('metadata', {}).get('source', 'Unknown Document')
            page = chunk.get('metadata', {}).get('page', 1)
            text = chunk.get('text', '')
            reference_text += f"\n- Document: {source} (Page {page})\n  Excerpt: {text}\n"

        has_warnings = drug_alert.get('has_warnings', False)
        severity = drug_alert.get('severity', 'none')
        alert_desc = drug_alert.get('description', 'No local interaction warnings identified.')

        # Standard medical assistant system boundaries
        system_rules = (
            "You are a clinical pharmacist assistant acting on behalf of MedQuery. "
            "Formulate a helpful and structured drug safety recommendation. "
            "Prioritize warnings if active interactions exist, referencing source documents."
        )

        prompt = (
            f"User Question: {query}\n\n"
            f"--- DATABASE SAFETY ALERTS ---\n"
            f"Interaction Identified: {has_warnings}\n"
            f"Hazard Level: {severity.upper()}\n"
            f"Clinical Summary: {alert_desc}\n\n"
            f"--- REFERENCE CONTEXTS ---\n"
            f"{reference_text}\n\n"
            f"Please generate a clinical response in structured markdown. "
            f"Address any drug interactions explicitly and list citations with page numbers."
        )

        # Fallback to simulation if api key is missing
        if not api_key:
            print("Warning: GEMINI_API_KEY environment variable is blank. Utilizing local mock responder.")
            return LLMService._mock_gemini_generation(query, has_warnings, severity, alert_desc, contexts)

        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            
            # Try models in order of preference
            models_to_try = ['gemini-2.5-flash', 'gemini-2.0-flash', 'gemini-1.5-flash']
            
            for model_name in models_to_try:
                try:
                    # Using the latest Gemini models for fast and cost-effective clinical outputs
                    model = genai.GenerativeModel(
                        model_name=model_name,
                        system_instruction=system_rules
                    )
                    response = model.generate_content(prompt)
                    return response.text
                except Exception as model_err:
                    print(f"Gemini API model {model_name} invocation failed: {model_err}.")
            
            raise RuntimeError("All configured Gemini models failed to generate content.")
            
        except Exception as api_err:
            print(f"Gemini API invocation failed: {api_err}. Reverting to offline mockup.")
            return LLMService._mock_gemini_generation(query, has_warnings, severity, alert_desc, contexts)

    @staticmethod
    def _mock_gemini_generation(query, has_warnings, severity, alert_desc, contexts):
        """
        Creates simulated clinical answers for demonstration.
        """
        response_markdown = f"### 🩺 Clinical Consultation Summary: MedQuery Assistant\n\n"

        if has_warnings:
            response_markdown += (
                f"> [!WARNING]\n"
                f"> **Drug Interaction Risk Flagged**: `{severity.upper()}` Hazard Detected\n"
                f"> **Clinical Context**: {alert_desc}\n\n"
                f"**Clinical Recommendation**:\n"
                f"Concomitant administration of these active pharmaceutical compounds should be avoided or "
                f"managed with extreme caution. The risk profile outweighs standard benefits unless under "
                f"direct clinical specialist supervision.\n\n"
            )
        else:
            response_markdown += (
                f"**Clinical Assessment**: No direct drug-drug interaction warning matches were identified "
                f"in our primary catalogs for the queried compounds.\n\n"
            )

        response_markdown += "#### Verified Medical Literature Citations\n"
        for chunk in contexts:
            source = chunk.get('metadata', {}).get('source', 'ref_document')
            page = chunk.get('metadata', {}).get('page', 1)
            text_preview = chunk.get('text', '')[:150]
            response_markdown += f"- **{source} (Page {page})**: *\"{text_preview}...\"*\n"

        response_markdown += (
            f"\n\n---\n*Disclaimer: This response was generated by MedQuery's Offline Mock Engine because "
            f"no active GEMINI_API_KEY environment variable was configured.*"
        )
        
        return response_markdown
