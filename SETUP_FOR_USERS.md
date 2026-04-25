# 🚀 SETUP GUIDE FOR REPO USERS

## What Happens When Someone Clones Your Repo?

```
git clone <your-repo>
cd backend
```

They will see these files:
```
✅ requirements.txt (they'll use this!)
✅ app/           (source code)
✅ frontend/      (HTML, CSS, JS)
✅ data/          (foods.json, kb_mdg2020.md)
✅ README.md      (instructions)
✅ .gitignore     (rules for what's ignored)

❌ .venv/         (NOT there - git-ignored)
❌ __pycache__/   (NOT there - git-ignored)
❌ app.db         (NOT there - will be created fresh)
❌ chroma/        (NOT there - will be created by ingest.py)
❌ .env           (NOT there - they create their own)
```

---

## What They Do Next (Your Instructions Are in README.md)

```powershell
# 1. Create virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2. Install dependencies (from requirements.txt)
pip install -r requirements.txt

# 3. Ingest data into ChromaDB
python -m app.rag.ingest

# 4. Run the app
uvicorn app.main:app --reload

# 5. Open browser
http://localhost:8000
```

---

## Before Committing to Git

✅ **DO THIS BEFORE YOUR FIRST `git push`:**

```powershell
# 1. Verify .gitignore exists and is correct
ls -la .gitignore

# 2. Check what would be committed (should NOT see .venv, app.db, chroma, __pycache__)
git status

# 3. Add all tracked files (source code, data, requirements, README)
git add .

# 4. Check status again - only source files should show
git status

# 5. Commit
git commit -m "Initial commit: RAG-based dietary advice system"

# 6. Push to GitHub
git push origin main
```

---

## File-by-File Checklist

| File/Folder | Git? | Why |
|---|---|---|
| `app/` | ✅ Add | Source code needed |
| `requirements.txt` | ✅ Add | Dependencies definition |
| `README.md` | ✅ Add | Setup instructions |
| `.gitignore` | ✅ Add | Tells git what to ignore |
| `data/foods.json` | ✅ Add | Part of dataset |
| `data/kb_mdg2020.md` | ✅ Add | Part of dataset |
| `frontend/` | ✅ Add | UI files |
| `.venv/` | ❌ Ignore | Too large (100MB+) |
| `__pycache__/` | ❌ Ignore | Auto-generated |
| `*.pyc` | ❌ Ignore | Python compiled files |
| `app.db` | ❌ Ignore | Local database |
| `chroma/` | ❌ Ignore | Will be rebuilt |
| `.env` | ❌ Ignore | Secrets/passwords |
| `.vscode/` | ❌ Ignore | Personal IDE settings |

---

## If You Accidentally Committed Something

```powershell
# Remove from git (but keep on disk)
git rm --cached app.db
git rm -r --cached .venv/
git rm -r --cached __pycache__/

# Commit the removal
git commit -m "Remove large files that shouldn't be tracked"
git push
```

---

## Summary: The User Flow

```
GitHub Repo                   User's Machine
    ↓                              ↓
requirements.txt    ←→ Clones → pip install -r
README.md           ←→          Follows setup
.gitignore          ←→          (already ignored)
app/                ←→          Runs locally
data/               ←→          Uses for RAG
frontend/           ←→          Opens UI

(NOT there)                      (User creates fresh)
.venv/              ·            python -m venv .venv
app.db              ·            Created by FastAPI
chroma/             ·            Created by ingest.py
```

✅ **Perfect!** People can now clone, install, and run your project independently!
