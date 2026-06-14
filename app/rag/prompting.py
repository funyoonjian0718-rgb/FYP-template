from __future__ import annotations

from typing import Any

from app.rag.types import RetrievedSnippet


def _safe_value(value: Any) -> str | None:
    if value is None:
        return None

    text = str(value).strip()

    if not text or text.lower() in {"nan", "none", "null"}:
        return None

    return text


def _format_price(value: Any) -> str | None:
    if value is None:
        return None

    try:
        return f"RM {float(value):.2f}"
    except (TypeError, ValueError):
        return str(value)


def _question_flags(question: str) -> dict[str, bool]:
    q = question.lower()

    meal_plan = any(
        word in q
        for word in [
            "meal plan",
            "meal prep",
            "eating strategy",
            "breakfast",
            "lunch",
            "dinner",
            "snack",
            "7-day",
            "5-day",
            "daily",
        ]
    )

    budget = any(
        word in q
        for word in [
            "budget",
            "cost",
            "cheap",
            "affordable",
            "rm",
            "under rm",
        ]
    )

    compare = any(
        word in q
        for word in [
            "compare",
            "rank",
            "healthier",
            "which is healthier",
        ]
    )

    medical = any(
        word in q
        for word in [
            "diabetes",
            "diabetic",
            "hypertension",
            "blood pressure",
            "ckd",
            "kidney",
            "gout",
            "allergy",
            "lactose",
            "iron deficiency",
            "anemia",
            "anaemia",
        ]
    )

    return {
        "meal_plan": meal_plan,
        "budget": budget,
        "compare": compare,
        "medical": medical,
    }


def build_prompt(
    *,
    user_context: dict,
    question: str,
    selected_food: str | None,
    portion: str | None,
    retrieved: list[RetrievedSnippet],
    food_metadata: list[dict] | None = None,
) -> str:
    flags = _question_flags(question)

    context_lines: list[str] = []

    for i, r in enumerate(retrieved, start=1):
        context_lines.append(
            f"[{i}] Source: {r.source}\nSnippet: {r.snippet}"
        )

    context_block = (
        "\n\n".join(context_lines)
        if context_lines
        else "(no retrieved context)"
    )

    pricing_lines: list[str] = []

    if food_metadata:
        for item in food_metadata:
            name = _safe_value(item.get("name")) or "Unknown food"
            serving = _safe_value(item.get("serving_size")) or "one serving"

            line = f"- {name}: {serving}"

            field_map = [
                ("calories", "kcal"),
                ("carbohydrates_g", "g carbs"),
                ("protein_g", "g protein"),
                ("fat_g", "g fat"),
                ("fibre_g", "g fibre"),
                ("sugar_g", "g sugar"),
                ("sodium_mg", "mg sodium"),
                ("potassium_mg", "mg potassium"),
                ("phosphorus_mg", "mg phosphorus"),
                ("iron_mg", "mg iron"),
            ]

            for key, label in field_map:
                value = _safe_value(item.get(key))
                if value is not None:
                    line += f", {value}{label if value[-1].isdigit() else ' ' + label}"

            gi = _safe_value(item.get("glycemic_index"))
            if gi:
                line += f", GI: {gi}"

            diabetes = _safe_value(item.get("diabetes_suitable"))
            if diabetes:
                line += f", diabetes_suitable: {diabetes}"

            price = _format_price(item.get("price_myr"))
            if price:
                line += f", price: {price}"

            pricing_lines.append(line)

    pricing_block = (
        "\n".join(pricing_lines)
        if pricing_lines
        else "(no food nutrition or pricing metadata available)"
    )

    task_instruction = ""

    if flags["meal_plan"]:
        task_instruction += """
The user is asking for a meal plan, eating strategy, or meal prep.
You MUST include these exact sections:
- Breakfast
- Lunch
- Dinner
- Snacks/Drinks
- Budget Guidance

If the constraints are impossible, do NOT invent a fake perfect plan.
Instead, clearly say the plan is not fully feasible, explain which constraints conflict, and give the safest closest alternative.
"""

    if flags["budget"]:
        task_instruction += """
The user has a budget or cost constraint.
You MUST include Budget Guidance.
If exact prices are available, estimate cost using only those prices.
If exact prices are not available, say exact cost cannot be calculated from the knowledge base, then give low-cost strategy from retrieved context.
Do not skip the budget section.
"""

    if flags["compare"]:
        task_instruction += """
The user is asking for comparison or ranking.
You MUST include a simple comparison table or bullet comparison.
You MUST include a final ranking with reasons.
"""

    if flags["medical"]:
        task_instruction += """
The user has medical conditions or dietary risks.
Be conservative.
Do not diagnose.
Do not claim treatment or cure.
For CKD, hypertension, diabetes, gout, allergy, lactose intolerance, or iron deficiency, explain what nutrients or food types need caution based on retrieved context.
Always include a medical disclaimer.
"""

    return f"""You are a dietary advice assistant for Malaysia, powered by Retrieval-Augmented Generation (RAG).

IMPORTANT:
Your job is not only to repeat retrieved snippets.
Your job is to use the retrieved knowledge base to produce a useful, structured answer.

CRITICAL RULES:
1. Use the "Food Nutrition Data" and "Retrieved Context" as the factual source for food, nutrition, price, disease-specific advice, and alternatives.
2. Do not invent exact nutrition numbers, prices, sodium, potassium, phosphorus, iron, calories, or protein values that are not provided.
3. If an exact number is missing, say "not available in the knowledge base" instead of inventing it.
4. Do NOT immediately refuse just because some exact values are missing.
5. Only say "I don't have enough information in my knowledge base" if there is no relevant retrieved context at all.
6. Always cite retrieved sources using the source numbers like [1], [2], [3].
7. Do not recommend foods that violate explicit user restrictions.
   Example: if the user says no soy, do not recommend tofu, tempeh, soy milk, or soy-based foods.
8. If constraints conflict, clearly say the combination is difficult or not realistic.
9. If the user asks for breakfast/lunch/dinner, you MUST include breakfast/lunch/dinner headings.
10. If the user asks for budget, cost, affordable, RM, or under RM, you MUST include Budget Guidance.
11. If the user asks for a multi-day plan, provide a practical multi-day structure. If exact daily nutrition cannot be calculated, say so clearly.
12. Keep the answer practical for Malaysian users, especially students, mamak stalls, convenience stores, and local foods when those appear in retrieved context.

Task-Specific Instructions:
{task_instruction}

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

RETRIEVED CONTEXT:
{context_block}

User Question:
{question}

RESPONSE FORMAT:
Use clear headings. Do not write everything in one paragraph.

Feasibility and Safety Check:
- State whether the request is suitable, moderate, risky, or not fully feasible.
- Mention any conflicting constraints.

Summary Recommendation:
- Give the main recommendation in 2-4 sentences.

Meal Plan / Eating Strategy:
- Breakfast:
- Lunch:
- Dinner:
- Snacks/Drinks:

Budget Guidance:
- If prices are available, give an estimated cost.
- If exact prices are not available, say exact cost is not available in the knowledge base and give affordable strategy from retrieved sources.
- Do not skip this section if the user mentioned budget, RM, cheap, affordable, student, mamak, or convenience store.

Nutrition / Health Reasoning:
- Explain calories, protein, carbohydrate, sodium, sugar, fat, potassium, phosphorus, iron, GI, or other relevant concerns only when supported by retrieved context.
- If a required nutrient value is missing, say it is not available in the knowledge base.

Foods to Avoid or Modify:
- List foods that should be avoided, limited, or modified based on the user's restrictions and retrieved context.
- Explain why.

Better Alternatives:
1. Food name - reason.
2. Food name - reason.
3. Food name - reason.

Comparison / Ranking:
- Include this section if the user asks to compare or rank foods.
- If not relevant, write "Not applicable."

Sources Used:
- Cite the retrieved source numbers used, for example [1], [2], [3].

References from RAG:
- <Source name>: "<short supporting quote from retrieved context>"
- <Source name>: "<short supporting quote from retrieved context>"

Health Disclaimer:
- This is educational guidance only and not a medical diagnosis.
- For diabetes, CKD, hypertension, gout, allergy, pregnancy, or other medical conditions, the user should consult a doctor or registered dietitian.
"""