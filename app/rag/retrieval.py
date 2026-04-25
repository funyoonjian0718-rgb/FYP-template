from __future__ import annotations

import os

# Disable ChromaDB telemetry completely
os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")

import chromadb
from chromadb.config import Settings

from app.core.settings import settings
from app.rag.embedding import EmbeddingService
from app.rag.types import RetrievedSnippet


class RetrievalService:
    def __init__(self) -> None:
        os.makedirs(settings.chroma_dir, exist_ok=True)
        self._emb = EmbeddingService()
        self._client = chromadb.PersistentClient(
            path=settings.chroma_dir,
            settings=Settings(anonymized_telemetry=False)
        )
        self._col = self._client.get_or_create_collection(name="fyp_kb", metadata={"hnsw:space": "cosine"})

    def retrieve(self, query: str, *, k: int | None = None) -> list[RetrievedSnippet]:
        q_emb = self._emb.embed([query])
        res = self._col.query(
            query_embeddings=q_emb,
            n_results=k or settings.rag_top_k,
            include=["documents", "metadatas"],
        )

        snippets: list[RetrievedSnippet] = []
        docs = (res.get("documents") or [[]])[0]
        metas = (res.get("metadatas") or [[]])[0]
        for doc, meta in zip(docs, metas, strict=False):
            source = (meta or {}).get("source", "Unknown source")
            text = (doc or "").strip().replace("\n", " ")
            if len(text) > 260:
                text = text[:260].rstrip() + "…"
            if text:
                snippets.append(RetrievedSnippet(source=source, snippet=text))
        return snippets


retrieval_service = RetrievalService()

