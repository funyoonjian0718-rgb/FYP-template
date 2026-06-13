# 🔬 FYP — Context-Aware Dietary Advice (RAG-Based)

**AI-powered Malaysian dietary recommendation system using Retrieval-Augmented Generation (RAG).**

Demonstrates proper RAG architecture with separate concerns for user data (SQL) and knowledge base (vector DB).

---

## 🏗️ Final Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      User Interface (Web)                       │
│                                                                  │
│  Input: Food selection + Health context + Question             │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                      FastAPI Backend                            │
│  ├─ User authentication & profiles (JWT)                        │
│  └─ Query routing & response formatting                         │
└────────────────────────────┬────────────────────────────────────┘
                             │
        ┌────────────────────┴────────────────────┐
        │                                         │
┌───────▼──────────────┐             ┌──────────▼──────────┐
│   User Database      │             │   RAG Pipeline      │
│   (SQLite/MySQL)     │             │                     │
│                      │             │ 1. Embed query      │
│ ├─ users             │             │ 2. Search vectors   │
│ ├─ query_history     │             │ 3. Retrieve docs    │
│ └─ tokens            │             │ 4. Build prompt     │
└──────────────────────┘             │ 5. Call LLM         │
                                     └──────────┬──────────┘
                                                │
                        ┌───────────────────────┴─────────────────┐
                        │                                         │
                  ┌─────▼──────────┐                  ┌──────────▼────────┐
                  │   ChromaDB      │                  │  Ollama (LLM)     │
                  │ (Vector Store)  │                  │                   │
                  │                 │                  │ Model: llama3     │
                  │ ├─ Embeddings   │                  │ Task: Generate    │
                  │ ├─ Documents    │                  │ answer from       │
                  │ └─ Metadata     │                  │ context           │
                  │                 │                  │                   │
                  │ Vectorstore:    │                  └───────────────────┘
                  │ ./vectorstore/  │
                  └─────────────────┘

Data Sources Ingested into ChromaDB:
├─ Malaysian food nutrition (foods.json)
├─ Dietary guidelines (kb_mdg2020.md)
└─ USDA FoodData Central (CSV, optional)
```

---

## 🎯 Key Architectural Decisions

| Component | Technology | Role | Why |
|-----------|-----------|------|-----|
| **User Data** | SQLite/MySQL | Store users, queries, auth | SQL is best for structured, relational data |
| **Knowledge Base** | ChromaDB | Vector embeddings, semantic search | Perfect for RAG retrieval |
| **Embeddings** | SentenceTransformers | Convert text → vectors | Fast, accurate, no API needed |
| **LLM** | Ollama (llama3) | Generate answers | Local, private, offline-capable |
| **Data Format** | JSON, CSV, MD, TXT | Flexible input | Supports multiple data sources |

---

## 📊 Data Sources (IR Alignment)

Your system ingests 3 types of data:

1. **Malaysian Foods** (`foods.json`)
   - Nasi lemak, roti canai, nasi goreng, etc.
   - Nutritional values, GI, diabetes suitability
   - **Proves localization**

2. **Verified Guidelines** (`kb_mdg2020.md`)
   - WHO & MOH recommendations
   - Diabetes management protocols
   - **Ensures factual grounding**

3. **USDA Dataset** (optional CSV)
   - 10,000+ food items
   - Nutrition, allergens, serving sizes
   - **Demonstrates scale**

---

## ⚙️ How RAG Works (For IR)

### **Non-RAG Chatbot:**
```
User Question → LLM → Answer (hallucinated, no sources)
```

### **Your RAG System:**
```
User Question
    ↓
1. Embed question using SentenceTransformer
    ↓
2. Search ChromaDB for similar documents (top 4)
    ↓
3. Retrieve actual facts from Malaysian food data + guidelines
    ↓
4. Build prompt: "Use ONLY these retrieved documents"
    ↓
5. LLM generates answer grounded in facts
    ↓
6. Return: Answer + Retrieved Sources
```

**Result:** User sees **where** the answer came from ✅

---

## 🚀 Installation

### Prerequisites
- Python 3.10+
- Ollama installed and running (`ollama serve`)
- Model pulled: `ollama pull llama3`

### Setup (Windows PowerShell)

```powershell
# 1. Clone repo
cd backend

# 2. Create virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install -r requirements.txt

# 4. Ingest data into ChromaDB (first-time)
python -m app.rag.ingest

# Output should show:
# ✅ Ingestion complete!
#    Total chunks: 42
#    Guidelines: 10
#    Foods: 25
#    Datasets: 7
#    Vectorstore: ./vectorstore

# 5. Run backend
uvicorn app.main:app --reload

# Opens http://localhost:8000
```

---

## 📥 Adding USDA Dataset (Optional)

To include USDA FoodData Central (proves "large dataset"):

1. **Download:**
   ```
   https://fdc.nal.usda.gov/download-datasets.html
   → Download "Branded Foods" CSV (~300MB)
   ```

2. **Extract & Move:**
   ```
   Move to: backend/data/FoodData_Central_*.csv
   ```

3. **Reingest:**
   ```powershell
   python -m app.rag.ingest
   ```

The script will automatically pick up the CSV and ingest ~5,000 rows.

---

## 🎮 Using the App

1. **Register & Login**
   ```
   http://localhost:8000
   ```

2. **Ask Dietary Questions**
   ```
   "Can I eat nasi lemak if I have diabetes?"
   "What should I eat for dinner after roti canai for lunch?"
   "Calculate sugar in my meal of roti canai + teh tarik + nasi goreng"
   ```

3. **See Results:**
   - ✅ AI answer grounded in retrieved context
   - ✅ Retrieved sources shown below answer
   - ✅ Query saved to history
   - ✅ Nutrition data displayed

---

## 📁 Directory Structure (IR-Relevant)

```
backend/
├── app/
│   ├── main.py                    # FastAPI app
│   ├── core/
│   │   ├── settings.py            # Config (vectorstore_dir, etc.)
│   │   └── security.py            # Auth (JWT, bcrypt)
│   ├── db/
│   │   ├── models.py              # User, QueryHistory (SQL)
│   │   └── session.py             # SQLAlchemy setup
│   ├── rag/
│   │   ├── ingest.py              # Load JSON/CSV/MD → ChromaDB ⭐
│   │   ├── retrieval.py           # Query ChromaDB ⭐
│   │   ├── generation.py          # Call Ollama LLM ⭐
│   │   ├── prompting.py           # Build RAG prompt ⭐
│   │   └── embedding.py           # SentenceTransformer ⭐
│   └── routes/
│       ├── query.py               # /diet/query (RAG endpoint)
│       ├── auth.py                # /auth/* (user mgmt)
│       └── ui.py                  # HTML templates
├── frontend/
│   ├── templates/
│   │   └── index.html             # Main UI (shows references)
│   └── static/
│       ├── css/style.css
│       └── js/app.js              # Handles RAG response display
├── data/
│   ├── foods.json                 # Malaysian foods nutrition ⭐
│   ├── kb_mdg2020.md              # Dietary guidelines ⭐
│   └── FoodData_Central_*.csv     # USDA dataset (optional) ⭐
├── vectorstore/                   # ChromaDB (auto-created)
│   └── (persisted embeddings)
├── app.db                          # SQLite (auto-created)
├── requirements.txt               # Python dependencies
├── .gitignore
└── README.md                       # This file
```

**⭐ = Critical for RAG**

---

## 🔍 IR Alignment Checklist

Your system demonstrates:

- ✅ **RAG Pipeline:** Query → Retrieve → Generate → Return sources
- ✅ **Vector Database:** ChromaDB persisting embeddings locally
- ✅ **Large Dataset:** USDA (10k+) + Malaysian foods + guidelines
- ✅ **Structured Output:** Answer + Retrieved sources + Metadata
- ✅ **Context-Aware:** User health profile considered
- ✅ **Fact-Grounded:** LLM forced to use retrieved context
- ✅ **Localized:** Malaysian-specific food + guidelines
- ✅ **Persistent Storage:** User history, query history
- ✅ **References Displayed:** Frontend shows sources

---

## 🛠️ Troubleshooting

| Issue | Fix |
|-------|-----|
| `Cannot connect to ChromaDB` | Run `python -m app.rag.ingest` first |
| `Ollama 500 error` | Run `ollama serve` in another terminal |
| `Port 8000 in use` | `uvicorn app.main:app --port 8001` |
| `No chunks ingested` | Check `data/` has `.json` or `.md` files |
| `Empty references` | ChromaDB may be empty; reingest |

---

## 📚 API Endpoints

### Public
- `GET /` — Login page
- `POST /auth/register` — Register user
- `POST /auth/login` — Login (returns JWT)

### Authenticated (Require Bearer token)
- `GET /diet/foods` — List available foods
- `POST /diet/query` — Ask dietary question ⭐
  ```json
  {
    "query_text": "Is nasi lemak okay?",
    "selected_food": "Nasi Lemak",
    "portion": "small",
    "free_text_food": null
  }
  ```
  Response:
  ```json
  {
    "formatted_answer": "Nasi lemak is not ideal...",
    "references": [
      {
        "source": "foods.json",
        "snippet": "Nasi lemak: high fat..."
      }
    ]
  }
  ```
- `GET /diet/history` — Query history (latest 10)

---

## 🔐 Security Notes

- JWT tokens stored in browser `localStorage`
- Passwords hashed with bcrypt
- `.env` ignored (secrets not in git)
- Ollama accessed locally only (no API key needed)

---

## 📈 Next Steps for Enhancement

1. **More Data:** Download full USDA dataset (200k+ foods)
2. **Fine-tuning:** Improve prompts based on user feedback
3. **Deployment:** Docker, AWS Lambda, or Azure Functions
4. **Monitoring:** Log queries, track system performance
5. **Personalization:** Store user preferences, meal plans
6. **Mobile:** React Native or Flutter frontend

---

## 📖 References

- [ChromaDB Docs](https://docs.trychroma.com/)
- [SentenceTransformers](https://www.sbert.net/)
- [Ollama](https://ollama.ai/)
- [USDA FoodData Central](https://fdc.nal.usda.gov/)
- [Malaysian Dietary Guidelines](https://www.moh.gov.my/)

---

## 📄 License

MIT
