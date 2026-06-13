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

Your migration is successful if:

- ✅ Ingestion completes with 40+ chunks
- ✅ Questions return answers (no "working..." forever)
- ✅ References appear with sources
- ✅ History saves and loads
- ✅ Multiple queries show different references
- ✅ No MySQL embeddings errors
- ✅ ./vectorstore/ folder exists and grows

---

## 🎓 What This Proves

For your IR submission, this setup demonstrates:

1. **Proper RAG Architecture**
   - ✓ Separate data stores (SQL + Vector DB)
   - ✓ Semantic retrieval
   - ✓ Context-grounded generation

2. **Large Dataset Support**
   - ✓ Ingests multiple formats (JSON, CSV, MD, TXT)
   - ✓ Converts foods to searchable text
   - ✓ Can scale to 10k+ documents

3. **Fact-Grounded AI**
   - ✓ Shows retrieved sources
   - ✓ LLM uses context only
   - ✓ No hallucinations

4. **Malaysian Localization**
   - ✓ Malaysian food database
   - ✓ Diabetes context
   - ✓ Local guidelines

---

## 📞 Need Help?

1. Check MIGRATION_GUIDE.md for detailed explanations
2. Review README.md for architecture overview
3. Check console logs for error messages
4. Verify Ollama is running: `ollama list`

---

**All tests passing? 🎉 You're ready for IR submission!**
