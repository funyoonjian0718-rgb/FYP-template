from __future__ import annotations

from app.rag.types import RetrievedSnippet


def build_prompt(
    *,
    user_context: dict,
    question: str,
    selected_food: str | None,
    portion: str | None,
    retrieved: list[RetrievedSnippet],
    food_metadata: list[dict] | None = None,
) -> str:
    context_lines = []
    for i, r in enumerate(retrieved, start=1):
        context_lines.append(f"[{i}] Source: {r.source}\nSnippet: {r.snippet}")

    context_block = "\n\n".join(context_lines) if context_lines else "(no retrieved context)"

    pricing_lines = []
    if food_metadata:
        for item in food_metadata:
            name = item.get("name")
            serving = item.get("serving_size", "one serving")
            price = item.get("price_myr")
            calories = item.get("calories")
            carbs = item.get("carbohydrates_g")
            protein = item.get("protein_g")
            fat = item.get("fat_g")
            fibre = item.get("fibre_g")
            sugar = item.get("sugar_g")
            sodium = item.get("sodium_mg")
            gi = item.get("glycemic_index")
            diabetes = item.get("diabetes_suitable")
            line = f"- {name}: {serving}"
            if calories is not None:
                line += f", {calories} kcal"
            if carbs is not None:
                line += f", {carbs}g carbs"
            if protein is not None:
                line += f", {protein}g protein"
            if fat is not None:
                line += f", {fat}g fat"
            if fibre is not None:
                line += f", {fibre}g fibre"
            if sugar is not None:
                line += f", {sugar}g sugar"
            if sodium is not None:
                line += f", {sodium}mg sodium"
            if gi:
                line += f", GI: {gi}"
            if diabetes is not None:
                line += f", diabetes_suitable: {diabetes}"
            if price is not None:
                line += f", price: RM {price:.2f}"
            pricing_lines.append(line)

    pricing_block = "\n".join(pricing_lines) if pricing_lines else "(no food nutrition or pricing metadata available)"

    return f"""You are a dietary advice assistant for Malaysia, powered by Retrieval-Augmented Generation (RAG).

**CRITICAL INSTRUCTIONS:**
1. You MUST ONLY use information from the "Retrieved Context" section below.
2. DO NOT use any prior knowledge about foods or nutrition not in the retrieved context.
3. If the context does not contain information to answer the question, respond: "I don't have enough information in my knowledge base to answer this. Please consult a dietitian."
4. ALWAYS cite which source(s) you used from the retrieved context.
5. Be cautious about medical claims and avoid medical diagnosis. If uncertain, defer to professional advice.
6. When multiple sources say different things, acknowledge the difference.

User Context:
- Type 2 Diabetes: {user_context.get("type2_diabetes")}
- Age: {user_context.get("age")}
- Weight (kg): {user_context.get("weight_kg")}
- Activity level: {user_context.get("activity_level")}

Food Context:
- Selected food: {selected_food}
- Free-text food: {user_context.get("free_text_food")}
- Portion: {portion}

Food Nutrition Data:
{pricing_block}

**RETRIEVED CONTEXT (USE ONLY THIS TO ANSWER):**
{context_block}

User Question:
{question}

**RESPONSE FORMAT:**
Answer in these sections:

Summary Recommendation:
[1-3 sentences using ONLY retrieved context]

Why (Based on Retrieved Context):
[2-6 bullet points, cite your sources]

Better Alternatives (From Retrieved Sources):
[3-6 Malaysian food options with reasons]

Portion Guidance (From Retrieved Context):
[Specific portion sizes with source citations]

Sources Used:
[List which sources from retrieved context you cited]

---
If constraints conflict, clearly state that the combination is difficult and offer the safest possible alternative.
If pricing data is available, use only the provided values and do not invent a different cost amount.
Do NOT recommend any foods that violate explicit user restrictions (for example, no soy if the user says "no soy").
Do NOT overstate the nutritional benefit of any single food without supporting evidence from the references.

References (from RAG):
- <Source name>: "<short quote/snippet>"
- <Source name>: "<short quote/snippet>"

Health Disclaimer:
<1-2 sentences stating this is not medical diagnosis and consult professionals>
"""

