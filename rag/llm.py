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

        # System boundaries supporting drug safety, general medical questions, and report summaries
        system_rules = (
            "You are an expert clinical pharmacist and medical assistant acting on behalf of MedQuery.\n"
            "Your duties include:\n"
            "1. Answering general medical and pharmaceutical questions thoroughly and accurately.\n"
            "2. If the user refers to or asks about their uploaded document, prescription, or medical report, "
            "summarize the content clearly (identifying active medications, dosages, instructions, or lab values) "
            "and suggest relevant standard treatments, drug safety warnings, and clinical precautions.\n"
            "3. If active drug-drug interactions are flagged in DATABASE SAFETY ALERTS, highlight them clearly and "
            "advise precautions.\n"
            "4. Provide references/citations to the source documents when referencing context.\n"
            "5. Always conclude with a professional medical disclaimer advising consultation with a healthcare provider."
        )

        prompt = (
            f"User Question: {query}\n\n"
            f"--- DATABASE SAFETY ALERTS ---\n"
            f"Interaction Identified: {has_warnings}\n"
            f"Hazard Level: {severity.upper()}\n"
            f"Clinical Summary: {alert_desc}\n\n"
            f"--- REFERENCE CONTEXTS (INCLUDING UPLOADED CLINICAL DOCUMENTS) ---\n"
            f"{reference_text}\n\n"
            f"Please generate a clinical response in structured markdown. "
            f"If the question pertains to summarizing or analyzing an uploaded medical report or prescription, "
            f"perform a full summary and suggest standard treatment options/clinical guidance. "
            f"Cite any reference documents and page numbers explicitly."
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
        Creates simulated clinical answers for demonstration when Gemini API is offline.
        """
        query_clean = query.lower()
        is_summary_query = any(k in query_clean for k in ['summarize', 'summary', 'report', 'prescription', 'upload', 'file', 'document'])
        is_general_medical_query = any(k in query_clean for k in ['what is', 'how to', 'how does', 'explain', 'treatment for', 'symptoms of', 'cause of', 'side effects'])

        if is_summary_query:
            response_markdown = f"### 📄 Medical Document Summary & Clinical Assessment\n\n"
            doc_content = ""
            source_file = "Uploaded Document"
            for chunk in contexts:
                if '[CONTENT OF UPLOADED DOCUMENT' in chunk['text']:
                    text_val = chunk['text']
                    source_file = chunk.get('metadata', {}).get('source', 'Uploaded Document')
                    # Extract raw text after header
                    header_end = text_val.find(']:')
                    if header_end != -1:
                        doc_content = text_val[header_end + 2:].strip()
                    else:
                        doc_content = text_val.strip()
                    break

            if doc_content:
                response_markdown += (
                    f"**Source Document Name**: `{source_file}`\n\n"
                    f"#### 🔍 Key Document Findings & Summary:\n"
                )
                
                # Split lines and identify potential medications/lab values
                lines = doc_content.split('\n')
                meds = []
                measurements = []
                for line in lines:
                    line_clean = line.lower()
                    if any(m in line_clean for m in ['mg', 'tablet', 'cap', 'daily', 'twice', 'rx', 'prescription', 'dose', 'aspirin', 'warfarin', 'lisinopril', 'ibuprofen', 'metformin', 'paracetamol', 'amoxicillin']):
                        meds.append(line.strip())
                    elif any(c in line_clean for c in ['bp', 'blood pressure', 'hba1c', 'cholesterol', 'creatinine', 'glucose', 'level', 'high', 'low', 'normal', 'positive', 'negative']):
                        measurements.append(line.strip())

                if meds:
                    response_markdown += "**Active Medications & Dosage Regimens**:\n"
                    for m in meds[:6]:
                        response_markdown += f"- {m}\n"
                    response_markdown += "\n"
                
                if measurements:
                    response_markdown += "**Vital Signs, Lab Diagnostics & Observations**:\n"
                    for m in measurements[:6]:
                        response_markdown += f"- {m}\n"
                    response_markdown += "\n"
                
                if not meds and not measurements:
                    # Provide snippet fallback
                    snippet = doc_content[:600] + "..." if len(doc_content) > 600 else doc_content
                    response_markdown += f"**Extracted Text Snippet**:\n```text\n{snippet}\n```\n\n"

                response_markdown += (
                    f"#### ⚕️ Suggested Treatment Guidelines & Clinical Considerations:\n"
                    f"1. **Dosing Verification**: Cross-reference active prescriptions with patient renal/hepatic clearance levels.\n"
                    f"2. **Therapeutic Duplications**: Monitor for therapeutic duplications, ensuring no multiple agents of the same class are prescribed concurrently.\n"
                    f"3. **Clinical Parameters**: Schedule regular diagnostic checks (e.g. renal function panels, HbA1c, or blood pressure monitoring) depending on the active therapy.\n\n"
                )
            else:
                response_markdown += (
                    f"> [!NOTE]\n"
                    f"> No uploaded medical reports or prescriptions were detected in the retrieval contexts. "
                    f"To generate a document summary, please upload a text or PDF file using the **Upload Desk** tab.\n\n"
                )

        elif is_general_medical_query:
            response_markdown = f"### 🩺 Medical Information & Clinical Guidance\n\n"
            response_markdown += f"**Subject**: Educational Review for *\"{query}\"*\n\n"
            
            # Formulate a structured educational response
            if 'metformin' in query_clean:
                response_markdown += (
                    f"**Pharmacological Class**: Biguanide oral antihyperglycemic agent.\n\n"
                    f"#### Clinical Mechanism of Action:\n"
                    f"- Decreases hepatic glucose production (gluconeogenesis).\n"
                    f"- Decreases intestinal absorption of glucose.\n"
                    f"- Improves insulin sensitivity by increasing peripheral glucose uptake and utilization.\n\n"
                    f"#### Standard Treatment Considerations:\n"
                    f"- **First-line therapy** for Type 2 Diabetes Mellitus.\n"
                    f"- Administered with meals to minimize gastrointestinal side effects (nausea, diarrhea).\n"
                    f"- Contraindicated in severe renal impairment (e.g. eGFR < 30 mL/min/1.73m²) due to risk of lactic acidosis.\n"
                )
            elif 'diabetes' in query_clean:
                response_markdown += (
                    f"#### Overview of Diabetes Mellitus:\n"
                    f"Diabetes Mellitus is a chronic metabolic disorder characterized by persistent hyperglycemia resulting "
                    f"from defects in insulin secretion, insulin action, or both.\n\n"
                    f"#### Types & Standard Treatments:\n"
                    f"1. **Type 1 Diabetes**: Absolute insulin deficiency. Requires lifelong basal-bolus insulin therapy.\n"
                    f"2. **Type 2 Diabetes**: Progressive insulin secretory defect on the background of insulin resistance. "
                    f"First-line pharmacological treatment is Metformin alongside lifestyle modifications (diet, exercise).\n\n"
                    f"#### Standard Clinical Monitoring:\n"
                    f"- **Hemoglobin A1c (HbA1c)**: Measure every 3–6 months (Target: typically < 7.0%).\n"
                    f"- **Blood Pressure & Lipid Profile**: Assess regularly to minimize cardiovascular complications.\n"
                )
            else:
                response_markdown += (
                    f"#### General Medical Principles:\n"
                    f"- **Indication & Assessment**: Medical treatments must be tailored to the individual patient's "
                    f"demographic, medical history, concurrent diseases, and genetic profile.\n"
                    f"- **Therapeutic Objectives**: Treatment targets are established to alleviate symptoms, arrest "
                    f"disease progression, and improve overall quality of life.\n"
                    f"- **Safety Monitoring**: Always perform appropriate diagnostic baseline tests (e.g., blood panels, "
                    f"liver/renal function checks) before initiating long-term pharmacotherapy.\n"
                )
            response_markdown += "\n"
        
        else:
            # Fall back to standard drug-drug interaction warning format
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
        citations_added = 0
        for chunk in contexts:
            # Exclude raw uploaded document content from citation lists if it's already rendered in summary
            if '[CONTENT OF UPLOADED DOCUMENT' in chunk['text']:
                continue
            source = chunk.get('metadata', {}).get('source', 'ref_document')
            page = chunk.get('metadata', {}).get('page', 1)
            text_preview = chunk.get('text', '')[:150]
            response_markdown += f"- **{source} (Page {page})**: *\"{text_preview}...\"*\n"
            citations_added += 1
            
        if citations_added == 0:
            response_markdown += "- *No local reference document matches cited for this query.*\n"

        response_markdown += (
            f"\n\n---\n*Disclaimer: This response was generated by MedQuery's Mock Clinical Engine (Offline Backup) "
            f"because no active GEMINI_API_KEY environment variable is configured or external APIs are unreachable. "
            f"Always consult a licensed medical physician or doctor before modifying any treatment guidelines.*"
        )
        
        return response_markdown
