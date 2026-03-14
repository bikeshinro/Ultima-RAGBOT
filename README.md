# Ultima — AI Assistant with RAG

Ultima is a production-floor AI assistant that uses **Retrieval-Augmented Generation (RAG)** to answer questions grounded in your own knowledge base. Users upload documents (PDF, DOCX, TXT), which are chunked, embedded, and stored in a vector database. When a question is asked, the most relevant chunks are retrieved and fed to an LLM to produce accurate, sourced answers.

Built with **Streamlit**, **MongoDB**, **Qdrant**, and swappable LLM/embedding backends (OpenAI, Ollama, Sentence-Transformers).

---

## Architecture & Flow

```
User (Streamlit UI)
  │
  ├─ Sign up / Login ──▶ MongoDB (users collection, bcrypt-hashed passwords, JWT auth)
  │
  ├─ Upload documents ──▶ Loader (PDF/DOCX/TXT)
  │                          │
  │                          ▼
  │                      Chunker (sentence-based, ~800 chars)
  │                          │
  │                          ▼
  │                      Embedding model (OpenAI / Ollama / Sentence-Transformers)
  │                          │
  │                          ▼
  │                      Qdrant (vector store — upsert with per-user filtering)
  │
  └─ Ask a question ───▶ Embed query
                            │
                            ▼
                        Qdrant search (top-K, score threshold, user-scoped)
                            │
                            ▼
                        Build prompt with retrieved contexts
                            │
                            ▼
                        LLM (OpenAI / Ollama) ──▶ Structured answer + sources
                            │
                            ▼
                        Chat history saved to MongoDB
```

---

## Project Structure

```
utltima/
├── .env                        # Environment variables (ports, keys, models)
├── docker-compose.yml          # MongoDB, Qdrant, Ollama, Streamlit services
├── Dockerfile                  # Streamlit container image
├── requirements.txt            # Python dependencies
├── main.py                     # Placeholder entry point
├── scripts/
│   ├── init_qdrant.py          # Create Qdrant collection with correct dimensions
│   ├── seed_demo_docs.py       # Bulk-ingest files from demo_docs/ folder
│   └── run_local.ps1           # PowerShell launcher script
└── src/
    ├── app.py                  # Streamlit UI (main application)
    ├── config.py               # Settings loaded from .env
    ├── auth/
    │   ├── auth_service.py     # Signup, login, JWT token generation
    │   └── password.py         # bcrypt hashing & verification
    ├── data/
    │   ├── loaders.py          # File readers (PDF, DOCX, TXT)
    │   ├── chunkers.py         # Sentence-based text splitter
    │   └── ingest.py           # Chunk, embed, upsert to Qdrant (with change detection)
    ├── db/
    │   ├── mongo.py            # MongoDB client, users/chats/messages collections
    │   └── qdrant.py           # Qdrant client, collection management, search, filters
    ├── llm/
    │   ├── embeddings.py       # Embedding providers (OpenAI, Ollama, Sentence-Transformers)
    │   ├── providers.py        # LLM chat providers (OpenAI, Ollama)
    │   ├── prompts.py          # System prompt and user prompt builder
    │   └── rag.py              # Retrieve contexts + generate answer
    └── models/
        ├── dtos.py             # Pydantic response DTOs
        └── schemas.py          # Pydantic data models (User, Chat, Message, Document)
```

---

## Prerequisites

- **Python 3.12+**
- **Docker & Docker Compose** (for MongoDB, Qdrant, Ollama)
- **OpenAI API key** (if using OpenAI as LLM/embedding provider)

---

## Environment Variables

Copy and configure the `.env` file in the project root. Key variables:

| Variable | Default | Description |
|---|---|---|
| `MONGO_URI` | `mongodb://admin:secret@localhost:27018` | MongoDB connection string |
| `MONGO_DB` | `ai_assistant` | Database name |
| `JWT_SECRET` | `replace_me` | Secret for signing JWT tokens — **change this** |
| `QDRANT_URL` | `http://localhost:6336` | Qdrant endpoint |
| `QDRANT_COLLECTION` | `knowledge_base` | Qdrant collection name |
| `EMBEDDING_MODEL` | `text-embedding-3-small` | Embedding model name |
| `LLM_PROVIDER` | `openai` | `openai`, `ollama`, or `sentence-transformers` |
| `LLM_MODEL` | `gpt-4o-mini` | LLM model name |
| `OPENAI_API_KEY` | — | Your OpenAI API key |

> **Port mapping note:** Docker Compose exposes MongoDB on host port **27018** and Qdrant on **6336**. The `.env` must use these host-side ports when running outside Docker.

---

## Getting Started

### Option A: Local Development (PowerShell)

**1. Start infrastructure services:**

```powershell
docker-compose up -d mongodb qdrant ollama
```

**2. Create and activate a virtual environment:**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**3. Install dependencies:**

```powershell
pip install -r requirements.txt
```

**4. Configure environment:**

Edit `.env` with your API keys and verify ports match your Docker setup.

**5. Initialize the Qdrant collection:**

```powershell
python -m scripts.init_qdrant
```

This probes the embedding model to determine vector dimensions and creates the collection automatically.

**6. (Optional) Seed demo documents:**

Place files in a `demo_docs/` folder at the project root, then:

```powershell
python -m scripts.seed_demo_docs
```

**7. Run the Streamlit app:**

```powershell
& ".venv\Scripts\python.exe" -m streamlit run src/app.py
```

The app will be available at [http://localhost:8501](http://localhost:8501).

### Option B: Full Docker Compose

```powershell
docker-compose up --build
```

This starts MongoDB, Qdrant, Ollama, and the Streamlit app. Access the UI at [http://localhost:8501](http://localhost:8501).

---
(Ultima.gif)
## How It Works

### Authentication
- Users sign up with an email and password (hashed with **bcrypt**).
- On login, a **JWT token** is issued and stored in the Streamlit session.
- All chat history and uploaded documents are scoped to the authenticated user.

### Document Ingestion
1. User uploads a file (PDF, DOCX, or TXT) via the Streamlit UI.
2. The file is parsed by the appropriate loader (`pypdf`, `python-docx`, or plain text).
3. Text is split into chunks (~800 characters) at sentence boundaries.
4. Each chunk is embedded using the configured embedding model.
5. Chunks are upserted into Qdrant with metadata (doc ID, user ID, source name, content hash).
6. **Change detection**: On re-upload, chunk hashes are compared — only changed documents are re-indexed.

### Question Answering (RAG)
1. The user's question is embedded using the same embedding model.
2. Qdrant performs a vector similarity search, filtered by user ID.
3. Results above the **score threshold** are selected as context.
4. A structured prompt is built with the retrieved contexts and sent to the LLM.
5. The LLM generates an answer following a template (Problem Statement, Causes, Actions, Safety Notes, Sources).
6. Both the question and answer are saved to MongoDB chat history.

### Swappable Providers
The UI sidebar lets users switch between providers at runtime:

| Component | Options |
|---|---|
| **LLM** | OpenAI (`gpt-4o-mini`, etc.), Ollama (local models) |
| **Embeddings** | OpenAI (`text-embedding-3-small`), Ollama, Sentence-Transformers (`all-MiniLM-L6-v2`) |

### Generation Settings
Adjustable from the sidebar:
- **Temperature** (0.0–1.0): Controls response creativity.
- **Top K documents** (1–10): Number of chunks to retrieve.
- **Score threshold** (0.0–1.0): Minimum similarity score to accept a chunk.

---

## Key Dependencies

| Package | Purpose |
|---|---|
| `streamlit` | Web UI framework |
| `pymongo` | MongoDB driver |
| `qdrant-client` | Qdrant vector database client |
| `openai` | OpenAI API (LLM + embeddings) |
| `sentence-transformers` | Local embedding models |
| `pypdf` | PDF text extraction |
| `python-docx` | DOCX text extraction |
| `bcrypt` | Password hashing |
| `pyjwt` | JWT token handling |
| `pydantic` | Data validation and schemas |

---

## Troubleshooting

- **`AttributeError: _dim`** — Make sure `rag.py` imports from `src.llm.embeddings` (not `embeddingsold`). The old module lacks dimension probing.
- **Qdrant dimension mismatch** — If you switch embedding models, delete and recreate the Qdrant collection by re-running `python -m scripts.init_qdrant` (you may need to delete the existing collection first via the Qdrant dashboard at `http://localhost:6336/dashboard`).
- **Port connection errors** — Verify `.env` ports match `docker-compose.yml` host-side mappings (MongoDB: `27018`, Qdrant: `6336`, Ollama: `11434`).
- **OpenAI auth errors** — Ensure `OPENAI_API_KEY` in `.env` has no leading spaces or surrounding quotes.
