# RAG Fix Guide for Complex Malaysian Dietary Questions

## Important finding
Your failure is not only because the food dataset is small. The screenshot errors such as “response does not clearly include breakfast planning”, “lunch planning”, “dinner planning”, and “budget guidance” are mostly **generation / prompt / retrieval design problems**.

A normal food table answers: “what is nasi lemak nutrition?”  
Your complex test questions require: meal-planning structure, disease rules, budget reasoning, feasibility checking, and comparison/ranking. That means the knowledge base should contain **food facts + rule chunks + scenario templates**.

This package gives you a 10,000-row multi-chunk RAG KB with these chunk types:

- `food_item` — nutrition and suitability facts for foods.
- `meal_time_use` — breakfast/lunch/dinner/snack usage rows so retrieval can trigger meal sections.
- `condition_food_rule` — diabetes, hypertension, CKD, gout, iron deficiency, lactose intolerance, muscle gain, fat loss and vegan keto rules for each food.
- `scenario_answer_template` — high-value templates for your exact complex questions and similar versions.

## Recommended file to ingest
Use:

`malaysian_diet_rag_10000_multichunk_kb.csv`

Embed only this column:

```python
text_to_embed = row["rag_text"]
```

Store metadata fields such as:

```python
metadata = {
    "kb_id": row["kb_id"],
    "chunk_type": row["chunk_type"],
    "title": row["title"],
    "base_food_name": row["base_food_name"],
    "category": row["category"],
    "meal_time": row["meal_time"],
    "diet_tags": row["diet_tags"],
    "health_tags": row["health_tags"],
    "budget_myr_per_serving": row["budget_myr_per_serving"]
}
```

## Retrieval settings that should work better
Do not retrieve only top 3 chunks. Use at least:

```python
TOP_K = 20
```

For complex dietary questions, retrieve from multiple angles:

1. Original user query.
2. Extracted foods, e.g. `nasi lemak roti canai maggi goreng chicken rice`.
3. Extracted conditions, e.g. `hypertension iron deficiency low sodium comparison`.
4. Meal-planning terms, e.g. `breakfast lunch dinner budget meal plan`.
5. Safety terms, e.g. `CKD potassium phosphorus sodium renal dietitian`.

Then combine and deduplicate retrieved chunks before sending to the LLM.

## Generator prompt you should use after retrieval
Use this after you retrieve the KB chunks:

```text
You are a Malaysian dietary recommendation assistant for an educational FYP prototype.
Use the retrieved knowledge base only for food facts and guideline rules.

When the user asks for a meal plan, your answer MUST include:
1. A short feasibility/safety check.
2. Breakfast planning.
3. Lunch planning.
4. Dinner planning.
5. Snacks/drinks if relevant.
6. Estimated cost per day or per week if a budget is mentioned.
7. Foods to avoid or modify and the reason.
8. A brief disclaimer for medical conditions such as CKD, diabetes, hypertension, gout, allergies or pregnancy.

If the user constraints are impossible, say they are not realistically achievable. Do not invent fake meals just to satisfy impossible macros or budget.

For comparison questions, include a table and ranking.
For myth/science questions, clearly answer true/false first, then explain.
```

## Why your previous RAG only answered 2/9
Most likely causes:

- The retriever found only food rows, not planning rules.
- Top-k was too small.
- The prompt did not force breakfast/lunch/dinner/budget sections.
- The model was not told how to handle impossible constraints.
- Disease constraints like CKD + hypertension + gout require rule chunks, not just calories/carbs/protein.

## Warning
The nutrition and mineral values in the generated KB are suitable for prototype retrieval and testing. They are not medical-grade values. For a final healthcare system, validate values against official sources and include clinician-reviewed rules.
