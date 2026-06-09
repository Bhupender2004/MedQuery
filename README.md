# MedQuery – AI Powered Drug Interaction Assistant

MedQuery is a production-grade AI-powered web portal built to analyze drug interactions, query medical documents, and present safety-first dashboards for healthcare professionals and clinical operators. 

The application utilizes a Retrieval-Augmented Generation (RAG) pipeline to cross-examine user queries against local medical documents embedded inside a vector database and maps them against structured drug interaction rules.

## Tech Stack
* **Backend**: Python 3.12+, Flask
* **Database**: MySQL (relational metadata, logs), ChromaDB (vector storage)
* **AI & NLP**: Sentence Transformers (local embeddings), Google Gemini API (orchestration & reasoning)
* **Frontend**: HTML5, Vanilla CSS (dynamic HSL tokens, glassmorphism), Vanilla JavaScript
* **ORM & Driver**: SQLAlchemy, PyMySQL

---

## Project Structure

```text
MedQuery/
├── app.py                     # Flask Application Factory setup & extension registration
├── run.py                     # Entry point scripts for local development runs
├── config/
│   ├── settings.py            # Environment-variable loading & schema validation
│   └── __init__.py            # Config package exporter
├── database/
│   ├── connection.py          # SQLAlchemy engine creation & scoped session mappings
│   ├── schema.sql             # SQL DDL schemas for references & database setup
│   └── __init__.py            # DB access layers
├── models/
│   ├── document_model.py      # SQLAlchemy model representing uploads metadata
│   ├── query_model.py         # SQLAlchemy model representing chat histories & citations
│   ├── drug_model.py          # SQLAlchemy model representing structured drug alerts
│   └── __init__.py            # Exporter for easy ORM imports
├── routes/
│   ├── chat_routes.py         # REST endpoints for asking queries & checking safety
│   ├── upload_routes.py       # REST endpoints for document uploads & parsing queue
│   ├── dashboard_routes.py    # Controllers for analytical metrics & dashboard pages
│   └── __init__.py            # Blueprint registry mapping
├── services/
│   ├── chat_service.py        # Business handlers for queries & history logic
│   ├── upload_service.py      # Document validation & upload handling
│   ├── dashboard_service.py   # Analytical metrics aggregators
│   └── __init__.py            # Service package exports
├── rag/
│   ├── ingest.py              # Parses documents, segments text, inserts into vector DB
│   ├── chunking.py            # Logical text-splitting configurations
│   ├── embeddings.py          # Sentence-transformers offline vectors runner
│   ├── retrieval.py           # ChromaDB search queries & metadata filters
│   ├── llm.py                 # Gemini API integration wrapper with fallback mocks
│   ├── drug_checker.py        # Algorithmic drug-interaction validation engine
│   └── __init__.py            # Core RAG interface
├── static/
│   ├── css/style.css          # Styled stylesheets with premium themes and animations
│   └── js/
│       ├── chat.js            # Frontend chat interface logic
│       ├── upload.js          # File uploader and queue updates
│       └── dashboard.js       # Analytical data visualizer
├── templates/
│   ├── index.html             # Landing portal page
│   ├── chat.html              # Conversational interface with citation displays
│   ├── upload.html            # Drag-and-drop document upload desk
│   └── dashboard.html         # Interactive logs dashboard
├── datasets/
│   └── drug_interactions.csv  # Mock initial reference dataset of interactions
├── uploads/                   # Destination folder for raw document storage
├── chroma_db/                 # Persistent local directory for vector storage
├── docs/                      # Architectural documents and contract sheets
├── tests/                     # Unit and integration tests
├── .env.example               # Template environment configuration variables
├── .gitignore                 # Files/folders excluded from source control
└── requirements.txt           # Declared project dependencies
```

---

## Installation & Setup

### 1. Clone & Configure Environments
Copy the sample environment configuration and fill in the required parameters (especially your Google Gemini API key):
```bash
cp .env.example .env
```

### 2. Set Up a Virtual Environment & Install Dependencies
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Initialize Database
Import `database/schema.sql` into your local MySQL server or verify connection strings match your settings in `.env`.

### 4. Running the Application
To boot up the local Flask development server, execute:
```bash
python run.py
```
The server will run on `http://127.0.0.1:5000/`.

---

## Architectural Principles
1. **Separation of Concerns**: Clean layers differentiate REST controllers (`routes/`), core business logic (`services/`), entity schemas (`models/`), database connections (`database/`), and AI processing (`rag/`).
2. **Robust Configuration**: All properties are consolidated in `config/settings.py` and validated on startup.
3. **Graceful Fallbacks**: RAG pipeline elements mock responses safely if secondary services (like vector DB or API servers) are offline.
