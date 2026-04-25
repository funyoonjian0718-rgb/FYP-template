# FYP — Context-Aware Dietary Advice (RAG + Ollama)

A **RAG-based dietary recommendation system** using Malaysian food data and verified guidelines.

**Architecture:**
```
User → FastAPI Backend → RAG Pipeline → ChromaDB → LLM (Ollama) → Structured Answer + References
```

**Features:**
- ✅ Diabetes-aware dietary advice (context-aware)
- ✅ Malaysian food & guidelines dataset
- ✅ RAG retrieval (semantic search)
- ✅ LLM generation (via Ollama)
- ✅ User authentication + query history
- ✅ Retrieved references displayed

---

## ⚙️ Prerequisites

### Required:
- **Python 3.10+** → [Download](https://www.python.org/)
- **Git** → [Download](https://git-scm.com/)
- **Ollama** (local LLM) → [Download](https://ollama.ai)

### Ollama Setup (First Time):
```powershell
# 1. Download & install from https://ollama.ai
# 2. Open PowerShell and run:
ollama serve

# 3. In another PowerShell window, pull the model:
ollama pull llama3

# 4. Verify it's installed:
ollama list
```

---

## 🚀 Installation (Windows)

### Step 1: Clone the Repository
```powershell
git clone <your-repo-url>
cd backend
```

### Step 2: Create Virtual Environment
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**Note:** If you get an execution policy error, run:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Step 3: Install Dependencies
```powershell
pip install -r requirements.txt
```

### Step 4: Ingest Data (First Time Only)
This loads Malaysian food data + guidelines into ChromaDB:
```powershell
python -m app.rag.ingest
```

Expected output:
```
Ingested 42 chunks into ./chroma
```

### Step 5: Run the App
```powershell
uvicorn app.main:app --reload
```

You'll see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

---

## 🌐 Using the App

1. **Open browser:** `http://localhost:8000`
2. **Register** a test account
3. **Login** 
4. **Ask a question:**
   - Example: *"Can I eat nasi lemak if I have diabetes?"*
   - Or: *"What should I eat for dinner after nasi lemak + teh tarik at lunch?"*
5. **See:**
   - ✅ Retrieved guidelines & food data
   - ✅ LLM-generated answer
   - ✅ Structured recommendations

**API Docs:** `http://localhost:8000/docs`

---

## 📁 What Gets Ignored (`.gitignore`)

**NOT pushed to repo** (automatically ignored):
- `.venv/` — Virtual environment (too large)
- `__pycache__/` — Python cache
- `app.db` — Database (rebuilds on user's machine)
- `chroma/` — Vector store (rebuilds via `ingest.py`)
- `.env` — Secrets (passwords, API keys)
- `.vscode/`, `.idea/` — IDE files

**Pushed to repo** (for users to clone):
- ✅ `requirements.txt` — Dependencies
- ✅ `app/` — Source code
- ✅ `frontend/` — HTML, CSS, JS
- ✅ `data/` — Malaysian food data + guidelines
- ✅ `README.md` — Setup instructions
- ✅ `.gitignore` — Ignore rules

---

## 🔧 Configuration (Optional)

### Using Environment Variables
Create a `.env` file (git-ignored):
```
DATABASE_URL=sqlite:///./app.db
JWT_SECRET=your-secret-key-here
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3
CHROMA_DIR=./chroma
RAG_TOP_K=4
```

**See** `app/core/settings.py` for defaults.

### Using MySQL (Optional)
```
DATABASE_URL=mysql+pymysql://root:password@localhost:3306/fyp_rag
```

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| `Cannot connect to Ollama` | Run `ollama serve` in a separate terminal |
| `Model not found` | Run `ollama pull llama3` |
| `Ollama crashed (500 error)` | Restart: `ollama serve` |
| `Port 8000 already in use` | Change port: `uvicorn app.main:app --port 8001` |
| `Database locked` | Delete `app.db` and restart |
| `ChromaDB empty` | Run `python -m app.rag.ingest` again |

---

## 📊 Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI app
│   ├── core/
│   │   ├── settings.py      # Config (LLM, DB, RAG)
│   │   └── security.py      # Auth (JWT, passwords)
│   ├── db/
│   │   ├── models.py        # User, QueryHistory tables
│   │   └── session.py       # SQLAlchemy setup
│   ├── auth/
│   │   ├── schemas.py       # Register/Login validation
│   │   └── deps.py          # Auth dependency
│   ├── rag/
│   │   ├── ingest.py        # Load data → ChromaDB
│   │   ├── retrieval.py     # Vector search
│   │   ├── generation.py    # LLM calls (Ollama)
│   │   ├── prompting.py     # Prompt engineering
│   │   ├── schemas.py       # Request/Response models
│   │   └── service.py       # RAG pipeline
│   └── routes/
│       ├── auth.py          # /auth/register, /auth/login
│       ├── query.py         # /diet/query (RAG endpoint)
│       └── ui.py            # Frontend pages
├── frontend/
│   ├── templates/           # HTML files
│   └── static/              # CSS, JS
├── data/
│   ├── foods.json           # Nutrition data
│   └── kb_mdg2020.md        # Malaysian guidelines
├── requirements.txt         # Python dependencies
├── .gitignore              # Git ignore rules
└── README.md               # This file
```

---

## 📚 How RAG Works

1. **Ingest** (`ingest.py`):
   - Reads `data/*.md` + `data/*.txt`
   - Chunks into 700-char pieces
   - Embeds using SentenceTransformers
   - Stores in ChromaDB

2. **Retrieve** (`retrieval.py`):
   - User asks a question
   - Embed question with same model
   - Find top-4 similar chunks

3. **Generate** (`generation.py`):
   - Pass question + chunks to Ollama
   - LLM generates answer grounded in data
   - Return answer + source references

---

## 🎯 Next Steps

- Add more Malaysian food data
- Fine-tune prompts for better answers
- Deploy to cloud (AWS, Azure, Heroku)
- Add vector search tuning (k, similarity threshold)
- Integrate with real nutrition APIs

---

## 📝 License

MIT (or specify your license)
