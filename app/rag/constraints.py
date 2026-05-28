from __future__ import annotations

import re

CONFLICTING_KETO = [
    "rice",
    "oats",
    "quinoa",
    "bread",
    "pasta",
    "potato",
    "banana",
    "corn",
    "lentil",
    "bean",
    "soy",
    "tofu",
    "tempeh",
    "miso",
    "natto",
    "chickpea",
    "kidney bean",
    "black bean",
    "lentils",
    "brown rice",
    "white rice",
]

CONFLICTING_VEGAN = [
    "chicken",
    "beef",
    "pork",
    "fish",
    "shrimp",
    "egg",
    "cheese",
    "milk",
    "yogurt",
    "butter",
    "honey",
    "gelatin",
    "anchovy",
]

CONFLICTING_NO_SOY = [
    "tofu",
    "tempeh",
    "soy",
    "edamame",
    "miso",
    "natto",
    "soy milk",
    "soy sauce",
]

CONFLICTING_NO_NUTS = [
    "almond",
    "cashew",
    "peanut",
    "walnut",
    "pistachio",
    "hazelnut",
    "brazil nut",
    "macadamia",
    "pecan",
    "nut",
]

LOW_SODIUM_INDICATORS = [
    "soy sauce",
    "fish sauce",
    "processed",
    "instant noodle",
    "crisps",
    "canned",
    "pickled",
    "mamak",
    "fried",
    "soup",
    "stock cube",
]

MEAL_PLAN_TERMS = ["7-day", "7 day", "weekly meal plan", "meal plan"]


def _contains_any(text: str, items: list[str]) -> bool:
    for item in items:
        if re.search(r"\b" + re.escape(item) + r"\b", text, re.IGNORECASE):
            return True
    return False


def normalize(text: str) -> str:
    return text.lower().strip()


def detect_constraints(question: str) -> dict[str, bool]:
    q = normalize(question)
    return {
        "keto": bool(re.search(r"\bketo\b", q)),
        "vegan": bool(re.search(r"\bvegan\b", q)),
        "no_soy": bool(re.search(r"no soy|soy-free|soy free", q)),
        "no_nuts": bool(re.search(r"no nuts|nut-free|nut free", q)),
        "low_sodium": bool(re.search(r"low sodium|low-sodium|hypertension|salt|sodium", q)),
        "meal_plan": _contains_any(q, MEAL_PLAN_TERMS),
        "budget": bool(re.search(r"rm\s*\d+|under rm\s*\d+|budget|per day", q)),
    }


def validate_answer(answer: str, question: str) -> list[str]:
    warnings: list[str] = []
    answer_text = normalize(answer)
    constraints = detect_constraints(question)

    if constraints["keto"]:
        if _contains_any(answer_text, CONFLICTING_KETO):
            warnings.append(
                "The response includes foods that are typically not keto-friendly."
            )

    if constraints["vegan"]:
        if _contains_any(answer_text, CONFLICTING_VEGAN):
            warnings.append(
                "The response includes animal-derived foods despite a vegan request."
            )

    if constraints["no_soy"]:
        if _contains_any(answer_text, CONFLICTING_NO_SOY):
            warnings.append(
                "The response includes soy-based foods despite a no-soy request."
            )

    if constraints["no_nuts"]:
        if _contains_any(answer_text, CONFLICTING_NO_NUTS):
            warnings.append(
                "The response includes nuts despite a no-nuts request."
            )

    if constraints["low_sodium"]:
        if _contains_any(answer_text, LOW_SODIUM_INDICATORS):
            warnings.append(
                "The response mentions high-sodium foods or ingredients, which conflicts with low-sodium/hypertension guidance."
            )

    if constraints["meal_plan"]:
        if not re.search(r"\bbreakfast\b", answer_text):
            warnings.append("The response does not clearly include breakfast planning.")
        if not re.search(r"\blunch\b", answer_text):
            warnings.append("The response does not clearly include lunch planning.")
        if not re.search(r"\bdinner\b", answer_text):
            warnings.append("The response does not clearly include dinner planning.")
        if not _contains_any(answer_text, ["rm ", "cost", "budget", "per day"]):
            warnings.append("The response does not include any budget or cost guidance.")

    if constraints["budget"] and not _contains_any(answer_text, ["rm ", "cost", "budget", "per day"]):
        warnings.append(
            "The response does not include budget guidance even though a cost constraint appears to be requested."
        )

    return warnings
