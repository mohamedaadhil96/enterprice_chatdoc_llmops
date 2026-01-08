# 🚀 ChatDocAI: Enterprise-Grade RAG Assistant

**ChatDocAI** is a professional, full-stack AI application designed to transform your static documents into an interactive knowledge base. Built with precision for enterprise scalability, it features high-performance retrieval-augmented generation (RAG), persistent document storage, and a stunning modern interface.

![Full Walkthrough](docs/assets/full_video.gif)

![ChatDocAI Banner](https://img.shields.io/badge/Enterprise-Intelligence-blue?style=for-the-badge)
![Tech Stack](https://img.shields.io/badge/Stack-FastAPI%20|%20Postgres%20|%20React-darkgreen?style=for-the-badge)

---

## 🏗️ System Architecture

Our architecture is designed for speed, security, and enterprise reliability.

![ChatDocAI Layered Architecture Diagram](docs/assets/architecture_diagram.png)

```mermaid
graph TD
    subgraph ClientLayer ["📱 CLIENT LAYER"]
        UI["React Frontend (Vite)"]
    end

    subgraph APILayer ["⚙️ API LAYER (FastAPI)"]
        Router["API Router"]
        JWT["JWT Auth Middleware"]
        ChatRouter["Chat Router"]
        Router --> JWT --> ChatRouter
    end

    subgraph CoreLayer ["🧠 CORE SERVICES LAYER"]
        RAG["RAG Orchestration"]
        LLM["LLM Service (Groq/Gemini)"]
        Memory["Session Memory Manager"]
        Embed["Embedding Model"]
        RAG --> LLM
        RAG --> Memory
        RAG --> Embed
    end

    subgraph DataLayer ["💾 DATA LAYER"]
        PG[("PostgreSQL DB")]
        FAISS[("FAISS Vector Index")]
    end

    subgraph IngestionLayer ["📥 DATA INGESTION PIPELINE"]
        Ext["Document Extractor"]
        Split["Text Splitter"]
        IngEmbed["Embedder"]
        Ext --> Split --> IngEmbed --> FAISS
    end

    UI --> Router
    ChatRouter --> RAG
    Memory --> PG
    Embed --> FAISS
```

## 📁 Project Structure

### Backend
```text
ChatDocAI/
├── main.py                    # FastAPI Entry point & Auth/Chat/Upload routes
├── migrate_to_postgres.py     # JSON to PostgreSQL migration script
├── multi_doc_chat/            # Core Backend Package
│   ├── config/                # App Configuration
│   │   └── config.yaml        # Component & Chain settings
│   ├── exception/             # Error Handling
│   │   └── custom_exception.py
│   ├── logger/                # Structured Logging
│   │   └── cutom_logger.py
│   ├── model/                 # Pydantic Schemas (API Data Models)
│   │   └── models.py
│   ├── prompts/               # RAG Prompt Engineering
│   │   └── prompt_library.py
│   ├── src/                   # Domain Services
│   │   ├── document_chat/     # RAG Retrieval Logic
│   │   │   └── retrieval.py   # LangChain & FAISS Integration
│   │   └── document_ingestion/# Document Processing
│   │       └── data_ingestion.py # Parser, Splitter & Indexer
│   └── utils/                 # Shared Utilities
│       ├── auth.py            # JWT, Password Hashing & Auth Dependency
│       ├── db.py              # SQLAlchemy DB Initialization
│       ├── models.py          # SQLAlchemy ORM Entities
│       ├── session_store.py   # PostgreSQL-backed Session Logic
│       ├── model_loader.py    # LLM & Embedding Model Initializers
│       ├── document_ops.py    # File Management Utilities
│       └── config_loader.py   # YAML & Env Variable Loader
├── docs/                      # Documentation Assets
│   └── assets/                # Architecture Diagrams
├── Dockerfile                 # Containerization Config
├── requirements.txt           # Python Dependencies
└── .gitignore                 # Secure Git Exclusion Rules
```

### Frontend
```text
frontend/
├── src/
│   ├── components/      # React UI components (Auth, Chat, Sidebar)
│   ├── api.js           # Axios base configuration
│   ├── App.jsx          # Main application layout
│   └── index.css        # Enterprise design system tokens
└── tailwind.config.js   # Tailwind v4 configuration
```

---

## ✨ Key Features

- **🛡️ Enterprise Security**: Robust JWT-based authentication with encrypted password hashing.
- **⚡ Advanced RAG**: Powered by Groq/Gemini for ultra-fast intelligent responses using MMR (Maximal Marginal Relevance) for diverse retrieval.
- **🗄️ Relational Persistence**: Powered by PostgreSQL for managing millions of user sessions and chronologically ordered chat histories.
- **🎨 Modern UI**: Arctic White enterprise design with glassmorphism, smooth animations, and a responsive layout.
- **📊 Real-time Feedback**: Multi-stage indexing animations providing visibility into the document analysis pipeline.
- **📂 Multi-Format Support**: Intelligent parsing for PDF, DOCX, and TXT files.

---

## 🛠️ Technology Stack

### Backend
- **Framework**: FastAPI (High Performance)
- **Database**: PostgreSQL (Relational Data)
- **ORM**: SQLAlchemy
- **AI/LLM**: LangChain, Groq, Google Generative AI
- **Vector Store**: FAISS
- **Authentication**: JWT (python-jose + passlib)

### Frontend
- **Library**: React 19 (Vite)
- **Styling**: Tailwind CSS v4
- **Animations**: Framer Motion
- **Icons**: Lucide React
- **API Client**: Axios

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.10+
- Node.js 18+
- PostgreSQL Instance

### 2. Backend Setup
```bash
# Clone the repository
git clone https://github.com/yourusername/ChatDocAI.git
cd ChatDocAI

# Install dependencies
pip install -r requirements.txt

# Configure Environment Variables (.env)
DATABASE_URL=postgresql://user:password@localhost:5432/doc_chat
GROQ_API_KEY=your_key_here
GOOGLE_API_KEY=your_key_here
SECRET_KEY=your_secret_for_jwt
```

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### 4. Database Initialization
The application automatically creates the required tables on the first run via `init_db()`. If you have legacy JSON data, use our migration script:
```bash
python migrate_to_postgres.py
```

---
