from __future__ import annotations

import os
from typing import Any

import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer

from app.core.settings import settings
from app.rag.types import RetrievedSnippet


class RetrievalService:
    """
    Better retrieval for complex dietary questions.

    Improvements:
    1. Uses higher top_k for complex meal-plan questions.
    2. Creates multiple search queries from one complex user question.
    3. Retrieves condition rules + food facts + budget/meal-time chunks.
    4. Deduplicates repeated ChromaDB results.
    """

    def __init__(self) -> None:
        os.makedirs(settings.vectorstore_dir, exist_ok=True)

        self._model = SentenceTransformer(settings.embedding_model)

        self._client = chromadb.PersistentClient(
            path=settings.vectorstore_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )

        self._collection = self._client.get_or_create_collection(
            name="dietary_kb",
            metadata={"hnsw:space": "cosine"},
        )

    def _has_any(self, text: str, words: list[str]) -> bool:
        return any(word in text for word in words)

    def _build_search_queries(self, query: str) -> list[str]:
        """
        Turn one complex question into several focused retrieval queries.

        Example:
        User asks about CKD + hypertension + mamak + budget + 7-day plan.
        A single embedding may miss some requirements.
        So we search multiple focused queries.
        """
        q = query.lower().strip()

        queries: list[str] = [query]

        # Meal plan / meal prep / daily eating structure
        if self._has_any(
            q,
            [
                "meal plan",
                "eating strategy",
                "meal prep",
                "breakfast",
                "lunch",
                "dinner",
                "snack",
                "7-day",
                "5-day",
                "daily",
            ],
        ):
            queries.append(
                "meal plan breakfast lunch dinner snacks drinks daily structure affordable Malaysian foods"
            )

        # Budget / cost
        if self._has_any(
            q,
            [
                "budget",
                "cost",
                "cheap",
                "affordable",
                "rm",
                "under rm",
                "student",
                "convenience store",
                "99 speedmart",
                "kk mart",
                "mamak",
            ],
        ):
            queries.append(
                "budget cost price RM affordable cheap student mamak convenience store Malaysian meal planning"
            )

        # Diabetes / low carb / keto / sugar
        if self._has_any(
            q,
            [
                "diabetes",
                "diabetic",
                "blood sugar",
                "low carb",
                "carb",
                "carbs",
                "ketogenic",
                "keto",
                "glycemic",
                "gi",
                "sugar",
            ],
        ):
            queries.append(
                "diabetes low glycemic index carbohydrate sugar low carb keto Malaysian food portion advice"
            )

        # Hypertension / sodium
        if self._has_any(
            q,
            [
                "hypertension",
                "blood pressure",
                "sodium",
                "salt",
                "low-sodium",
                "low sodium",
            ],
        ):
            queries.append(
                "hypertension low sodium salt blood pressure avoid processed foods instant noodles canned soup fried chicken"
            )

        # CKD / kidney / potassium / phosphorus
        if self._has_any(
            q,
            [
                "chronic kidney disease",
                "ckd",
                "kidney",
                "potassium",
                "phosphorus",
                "phosphate",
            ],
        ):
            queries.append(
                "chronic kidney disease CKD kidney diet controlled sodium potassium phosphorus protein Malaysian food"
            )

        # Gout / purine
        if self._has_any(q, ["gout", "purine", "uric acid"]):
            queries.append(
                "gout low purine uric acid avoid shellfish organ meats anchovies sardines Malaysian food"
            )

        # Iron deficiency / anemia
        if self._has_any(
            q,
            [
                "iron deficiency",
                "iron",
                "anaemia",
                "anemia",
                "haemoglobin",
                "hemoglobin",
            ],
        ):
            queries.append(
                "iron deficiency anemia high iron foods vitamin C Malaysian affordable protein"
            )

        # Allergy / lactose / restrictions
        if self._has_any(
            q,
            [
                "allergy",
                "allergic",
                "shellfish allergy",
                "lactose intolerance",
                "lactose",
                "no soy",
                "no nuts",
                "no coconut",
                "vegan",
                "halal",
            ],
        ):
            queries.append(
                "food restriction allergy lactose intolerance halal vegan no soy no nuts no coconut safe alternatives"
            )

        # Muscle gain / fat loss / protein
        if self._has_any(
            q,
            [
                "muscle",
                "gym",
                "protein",
                "gain",
                "fat loss",
                "lose weight",
                "weight loss",
                "exercise",
            ],
        ):
            queries.append(
                "high protein fat loss muscle gain calories protein Malaysian foods affordable"
            )

        # Comparison / ranking
        if self._has_any(q, ["compare", "rank", "healthier", "which is healthier"]):
            queries.append(
                "compare rank calories protein sodium iron healthier Malaysian dishes hypertension iron deficiency"
            )

        # Remove duplicates while keeping order
        unique_queries: list[str] = []
        seen: set[str] = set()

        for item in queries:
            cleaned = " ".join(item.split())
            if cleaned and cleaned not in seen:
                unique_queries.append(cleaned)
                seen.add(cleaned)

        # Too many queries can make retrieval noisy
        return unique_queries[:8]

    def _make_source_label(self, meta: dict[str, Any] | None) -> str:
        if not meta:
            return "Unknown"

        parts: list[str] = []

        for key in [
            "source",
            "row_type",
            "category",
            "food_name",
            "name",
            "condition",
            "meal_time",
        ]:
            value = meta.get(key)
            if value is not None and str(value).strip():
                parts.append(str(value).strip())

        return " | ".join(parts) if parts else "Unknown"

    def retrieve(self, query: str, *, k: int | None = None) -> list[RetrievedSnippet]:
        """
        Retrieve relevant chunks from ChromaDB.

        For simple questions: returns normal top_k.
        For complex questions: forces at least 20 chunks.
        """
        search_queries = self._build_search_queries(query)

        # For complex RAG, top 3/5 is usually too low
        requested_k = k or settings.rag_top_k
        final_k = max(requested_k, 20)

        # Retrieve this many per sub-query before deduplication
        per_query_k = min(max(final_k, 12), 30)

        query_embeddings = self._model.encode(
            search_queries,
            normalize_embeddings=True,
        ).tolist()

        results = self._collection.query(
            query_embeddings=query_embeddings,
            n_results=per_query_k,
            include=["documents", "metadatas", "distances"],
        )

        docs_nested = results.get("documents") or []
        metas_nested = results.get("metadatas") or []
        distances_nested = results.get("distances") or []
        ids_nested = results.get("ids") or []

        # Reciprocal rank fusion style scoring
        # This helps combine results from multiple subqueries.
        merged: dict[str, dict[str, Any]] = {}

        for query_index, docs in enumerate(docs_nested):
            metas = metas_nested[query_index] if query_index < len(metas_nested) else []
            distances = (
                distances_nested[query_index]
                if query_index < len(distances_nested)
                else []
            )
            ids = ids_nested[query_index] if query_index < len(ids_nested) else []

            for rank, doc in enumerate(docs):
                if not doc or not str(doc).strip():
                    continue

                meta = metas[rank] if rank < len(metas) else {}
                distance = distances[rank] if rank < len(distances) else None
                chroma_id = ids[rank] if rank < len(ids) else None

                snippet = str(doc).strip()

                # Prefer Chroma ID for deduplication. If unavailable, use snippet.
                dedupe_key = str(chroma_id) if chroma_id else snippet[:500]

                # Rank score: higher is better
                score = 1.0 / (60.0 + rank + 1.0)

                # Small distance bonus. Chroma cosine distance: lower is better.
                if distance is not None:
                    try:
                        score += max(0.0, 1.0 - float(distance)) * 0.01
                    except (TypeError, ValueError):
                        pass

                if dedupe_key not in merged:
                    merged[dedupe_key] = {
                        "score": 0.0,
                        "snippet": snippet,
                        "meta": meta,
                    }

                merged[dedupe_key]["score"] += score

        ranked = sorted(
            merged.values(),
            key=lambda item: item["score"],
            reverse=True,
        )

        snippets: list[RetrievedSnippet] = []

        for item in ranked[:final_k]:
            source = self._make_source_label(item.get("meta"))
            snippet = item.get("snippet", "").strip()

            if snippet:
                snippets.append(
                    RetrievedSnippet(
                        source=source,
                        snippet=snippet,
                    )
                )

        return snippets


retrieval_service = RetrievalService()