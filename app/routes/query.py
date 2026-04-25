import json
import os

from fastapi import APIRouter, Depends
from fastapi import HTTPException
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.db.models import QueryHistory, User
from app.db.session import get_db
from app.rag.schemas import DietaryQueryRequest, DietaryQueryResponse, ReferenceSnippet
from app.rag.service import rag_service


router = APIRouter()


@router.get("/foods")
def foods() -> list[str]:
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data"))
    path = os.path.join(base_dir, "foods.json")
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    # Support both old format (list of strings) and new format (list of objects)
    if isinstance(data, list) and len(data) > 0:
        if isinstance(data[0], dict):
            return [item["name"] for item in data]
        return data
    return []


@router.get("/foods/{food_name}")
def food_details(food_name: str) -> dict | None:
    """Get detailed nutrition information for a specific food."""
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data"))
    path = os.path.join(base_dir, "foods.json")
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict) and item.get("name", "").lower() == food_name.lower():
                return item
    return None


@router.post("/query", response_model=DietaryQueryResponse)
def dietary_query(
    payload: DietaryQueryRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DietaryQueryResponse:
    # Combine food context into the question to improve retrieval
    food_bits = []
    if payload.selected_food:
        food_bits.append(f"Selected dish: {payload.selected_food}")
    if payload.free_text_food:
        food_bits.append(f"Other food: {payload.free_text_food}")
    if payload.portion:
        food_bits.append(f"Portion: {payload.portion}")
    enriched_question = payload.query_text.strip()
    if food_bits:
        enriched_question = enriched_question + "\n\n" + "\n".join(food_bits)

    user_context = {
        "type2_diabetes": user.type2_diabetes,
        "age": user.age,
        "weight_kg": user.weight_kg,
        "activity_level": user.activity_level,
        "free_text_food": payload.free_text_food,
    }

    formatted, retrieved = rag_service.answer(
        user_context=user_context,
        question=enriched_question,
        selected_food=payload.selected_food,
        portion=payload.portion,
    )

    history = QueryHistory(
        user_id=user.id,
        query_text=payload.query_text,
        selected_food=payload.selected_food or payload.free_text_food,
        portion=payload.portion,
        response_text=formatted,
    )
    db.add(history)
    db.commit()

    refs = [ReferenceSnippet(source=r.source, snippet=r.snippet) for r in retrieved]
    return DietaryQueryResponse(formatted_answer=formatted, references=refs)


@router.get("/debug/retrieve")
def debug_retrieve(
    q: str,
    user: User = Depends(get_current_user),
):
    # Debug helper: verify RAG retrieval works independently of generation.
    # Auth required so you can keep it out of public demo if desired.
    if not q.strip():
        raise HTTPException(status_code=400, detail="q is required")
    retrieved = rag_service.retrieve(q)
    return [{"source": r.source, "snippet": r.snippet} for r in retrieved]


@router.get("/history")
def latest_history(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    rows = db.scalars(
        select(QueryHistory)
        .where(QueryHistory.user_id == user.id)
        .order_by(desc(QueryHistory.created_at))
        .limit(10)
    ).all()
    return [
        {
            "id": r.id,
            "query_text": r.query_text,
            "selected_food": r.selected_food,
            "portion": r.portion,
            "response_text": r.response_text,
            "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]

