# ✅ Post-Migration Testing Checklist

Complete these steps to verify the new RAG architecture is working correctly.

---

## 🔧 Setup Phase

- [ ] Clean environment:
  ```powershell
  rm -r chroma/        # Remove old ChromaDB
  rm -r vectorstore/   # Fresh vectorstore
  rm app.db            # Fresh database
  ```

- [ ] Reinstall dependencies (recommended):
  ```powershell
  pip install --upgrade -r requirements.txt
  ```

---

## 📥 Ingestion Phase

- [ ] Run new ingestion:
  ```powershell
  python -m app.rag.ingest
  ```

- [ ] Verify output includes all 3 sources:
  ```
  📖 Loading guidelines...   ✓
  🍜 Loading Malaysian foods... ✓
  📊 Loading CSV datasets...  ✓
  ```

- [ ] Check `./vectorstore/` folder created with data

- [ ] Verify chunk count matches (expect ~40+ chunks):
  ```
  ✅ Ingestion complete!
     Total chunks: 42+
     Guidelines: 5+
     Foods: 20+
     Datasets: 0 (unless CSV added)
  ```

---

## 🚀 Backend Phase

- [ ] Start FastAPI:
  ```powershell
  uvicorn app.main:app --reload
  ```

- [ ] Verify no errors in console output

- [ ] Check API docs available:
  ```
  http://localhost:8000/docs
  ```

---

## 🌐 Frontend Phase

- [ ] Open browser:
  ```
  http://localhost:8000
  ```

- [ ] See login page ✓

- [ ] Register test account:
  - Email: `test@example.com`
  - Password: `Test123!`
  - Diabetes: Yes
  - Age: 45
  - Weight: 75

- [ ] Login with test account ✓

- [ ] See food dropdown populated (should show Malaysian dishes)

---

## 🧪 RAG Query Phase

### Test 1: Basic Query
- [ ] Ask: `"Can I eat nasi lemak if I have diabetes?"`
- [ ] Verify:
  - ✓ Answer appears (not error)
  - ✓ References shown below answer
  - ✓ References include source (e.g., "foods.json")
  - ✓ Snippet text shown

### Test 2: With Selected Food
- [ ] Select: "Nasi Lemak" from dropdown
- [ ] Set portion: "Small"
- [ ] Ask: `"Is this okay for my dinner?"`
- [ ] Verify:
  - ✓ Food shown in answer
  - ✓ Portion considered
  - ✓ References updated
  - ✓ Nutrition data displayed

### Test 3: Complex Query
- [ ] Ask: `"Calculate sugar in roti canai + teh tarik + nasi goreng"`
- [ ] Verify:
  - ✓ Answer mentions all foods
  - ✓ References include guideline source
  - ✓ Nutritional breakdown visible

### Test 4: Multiple References
- [ ] Ask: `"What are better alternatives to nasi lemak?"`
- [ ] Verify:
  - ✓ At least 2-3 references shown
  - ✓ Each has source and snippet
  - ✓ References are relevant

---

## 💾 History Phase

- [ ] After asking questions, click "Load history (latest 10)"
- [ ] Verify:
  - ✓ Recent queries appear
  - ✓ Timestamps shown
  - ✓ Food selections saved
  - ✓ Responses preserved

---

## 🔍 Verification Details

### Check Logs
Look for these in console when asking a question:

```
INFO: POST /diet/query
# (No errors should follow)
```

### Check Response Format
Response should include:
```json
{
  "formatted_answer": "Nasi lemak is not ideal for...",
  "references": [
    {
      "source": "foods.json",
      "snippet": "Food: Nasi Lemak\nCalories: 450 kcal..."
    },
    {
      "source": "kb_mdg2020.md",
      "snippet": "For people with diabetes, choose foods with low..."
    }
  ]
}
```

### Check Vectorstore
```powershell
# Verify vectorstore exists and has data
ls -la vectorstore/
# Should show several files (not empty)
```

---

## 🐛 If Something Fails

### No references shown?
```powershell
# Vectorstore might be empty
python -m app.rag.ingest

# Then retry query
```

### "Cannot connect to Ollama"?
```powershell
# Start Ollama in another terminal
ollama serve

# Wait 5 seconds, then retry
```

### Query returns error?
```powershell
# Check all services running:
ollama list                          # Should show llama3
curl http://localhost:11434/api/tags  # Should return JSON
uvicorn app.main:app --reload      # Should show no errors
```

---

## ✨ Success Criteria

All of the following should pass:
- [ ] No Python errors during startup
- [ ] Database queries respond correctly
- [ ] ChromaDB retrieves relevant documents
- [ ] Ollama generates coherent answers
- [ ] Frontend displays results cleanly
- [ ] User can register and login
- [ ] Query history persists
- [ ] References are visible and accurate
