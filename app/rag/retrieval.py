from __future__ import annotations

from app.core.settings import settings
from app.rag.mysql_embeddings import MySQLEmbeddingService
from app.rag.types import RetrievedSnippet


class RetrievalService:
    def __init__(self) -> None:
        self._embeddings = MySQLEmbeddingService()

    def retrieve(self, query: str, *, k: int | None = None) -> list[RetrievedSnippet]:
        return self._embeddings.query(query, k=k or settings.rag_top_k)


retrieval_service = RetrievalService()

