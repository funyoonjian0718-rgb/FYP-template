from __future__ import annotations

from app.rag.types import RetrievedSnippet


def build_prompt(
    *,
    user_context: dict,
    question: str,
    selected_food: str | None,
    portion: str | None,
    retrieved: list[RetrievedSnippet],
) -> str:
    context_lines = []
    for i, r in enumerate(retrieved, start=1):
        context_lines.append(f"[{i}] Source: {r.source}\nSnippet: {r.snippet}")

    context_block = "\n\n".join(context_lines) if context_lines else "(no retrieved context)"

    return f"""You are a dietary advice assistant for Malaysia.
You MUST be cautious and avoid medical diagnosis. You MUST ground advice in the retrieved references.
If the references do not support a claim, say you are unsure and give a safer general suggestion.

User context:
- Type 2 Diabetes: {user_context.get("type2_diabetes")}
- Age: {user_context.get("age")}
- Weight (kg): {user_context.get("weight_kg")}
- Activity level: {user_context.get("activity_level")}

Food context:
- Selected food (dropdown): {selected_food}
- Free-text food: {user_context.get("free_text_food")}
- Portion: {portion}

Retrieved references (use these; cite by source name in the References section):
{context_block}

User question:
{question}

Return the answer in EXACTLY this format:

Summary Recommendation:
<1-3 sentences>

Nutritional Explanation (Why):
<2-6 bullet points>

Safer Alternatives:
<3-6 bullet points, Malaysian-appropriate where possible>

Portion Guidance:
<1-3 bullet points, use the provided portion if present>

References (from RAG):
- <Source name>: "<short quote/snippet>"
- <Source name>: "<short quote/snippet>"

Health Disclaimer:
<1-2 sentences stating this is not medical diagnosis and consult professionals>
"""

