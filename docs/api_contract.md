# MedQuery - API Specifications

This document defines the REST API contracts, headers, payloads, and status codes for **MedQuery**.

---

## 1. Chat Services

### POST `/api/chat/ask`
Submits a query to the conversational assistant for drug checking and reference search.

* **Headers**: `Content-Type: application/json`
* **Request Payload**:
  ```json
  {
    "query": "Can I take Aspirin with Warfarin?",
    "session_id": "demo-session-token"
  }
  ```
* **Response Payload (200 OK)**:
  ```json
  {
    "response": "### 🩺 Clinical Consultation Summary...\n\n> [!WARNING]\n> **Drug Interaction Risk Flagged**: `MAJOR` Hazard Detected\n> **Clinical Context**: Concomitant use increases bleed hazards...\n\n#### Verified Citations\n- **cardiovascular_safety_standards.pdf (Page 45)**...",
    "has_warnings": true,
    "severity": "major",
    "citations": [
      {
        "text": "Co-administering Aspirin and Warfarin significantly elevates hemorrhage hazards...",
        "metadata": {
          "source": "cardiovascular_safety_standards.pdf",
          "page": 45,
          "chunk_index": 0,
          "document_id": 12
        },
        "score": 0.91
      }
    ]
  }
  ```
* **Error Response (400 Bad Request)**:
  ```json
  {
    "error": "A non-empty query parameter is required."
  }
  ```

---

### GET `/api/chat/history`
Fetches a list of previous conversation logs for the specified session.

* **Query Parameters**: `session_id` (string, optional)
* **Response Payload (200 OK)**:
  ```json
  [
    {
      "id": 1,
      "session_id": "demo-session-token",
      "user_query": "Can I take Aspirin with Warfarin?",
      "ai_response": "### 🩺 Clinical Consultation...",
      "citations": "[{\"source\": \"cardiovascular_safety_standards.pdf\", \"page\": 45}]",
      "has_interaction_warnings": true,
      "severity_level": "major",
      "created_at": "2026-06-09T20:15:00"
    }
  ]
  ```

---

## 2. Ingestion Services

### POST `/api/upload`
Uploads a reference document file for ingestion and index partitioning.

* **Headers**: `Content-Type: multipart/form-data`
* **Request Payload**: Binary form parameter named `file` (supports `.pdf`, `.txt`, `.csv`).
* **Response Payload (222 Accepted)**:
  ```json
  {
    "message": "File uploaded and RAG ingestion sequence initiated successfully.",
    "document_id": 4,
    "filename": "renal_toxicology_handbook.pdf",
    "status": "processing"
  }
  ```
* **Error Response (400 Bad Request)**:
  ```json
  {
    "error": "Unsupported extension. Allowed extensions are: PDF, TXT, CSV."
  }
  ```

---

### GET `/api/upload/status/<int:document_id>`
Queries the vector parsing status of a document.

* **Response Payload (200 OK)**:
  ```json
  {
    "id": 4,
    "filename": "renal_toxicology_handbook.pdf",
    "filepath": "uploads/renal_toxicology_handbook.pdf",
    "file_size": 245120,
    "status": "completed",
    "created_at": "2026-06-09T20:16:10",
    "updated_at": "2026-06-09T20:16:15"
  }
  ```

---

## 3. Analytics Dashboard Services

### GET `/api/dashboard/stats`
Compiles global health summaries and query logs.

* **Response Payload (200 OK)**:
  ```json
  {
    "total_documents": 4,
    "total_queries": 24,
    "total_warnings": 8,
    "rules_count": 4,
    "severity_distribution": {
      "minor": 2,
      "moderate": 2,
      "major": 4
    },
    "recent_queries": [
      {
        "id": 24,
        "session_id": "demo-session-token",
        "user_query": "Can I take Aspirin with Warfarin?",
        "ai_response": "...",
        "citations": "...",
        "has_interaction_warnings": true,
        "severity_level": "major",
        "created_at": "2026-06-09T20:15:00"
      }
    ],
    "status": "active"
  }
  ```
