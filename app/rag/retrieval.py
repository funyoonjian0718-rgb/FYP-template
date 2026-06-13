from __future__ import annotations

import os
import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer

from app.core.settings import settings
from app.rag.types import RetrievedSnippet


class RetrievalService:
    def __init__(self) -> None:
        os.makedirs(settings.vectorstore_dir, exist_ok=True)
        self._model = SentenceTransformer(settings.embedding_model)
        self._client = chromadb.PersistentClient(
            path=settings.vectorstore_dir,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        self._collection = self._client.get_or_create_collection(
            name="dietary_kb",
            metadata={"hnsw:space": "cosine"}
        )

    def retrieve(self, query: str, *, k: int | None = None) -> list[RetrievedSnippet]:
        # Embed the query
        query_embedding = self._model.encode(query, normalize_embeddings=True).tolist()
        
        # Search ChromaDB
        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=k or settings.rag_top_k,
            include=["documents", "metadatas"]
        )
        
        # Convert to RetrievedSnippet objects
        snippets: list[RetrievedSnippet] = []
        docs = (results.get("documents") or [[]])[0]
        metas = (results.get("metadatas") or [[]])[0]
        
        for doc, meta in zip(docs, metas, strict=False):
            source = (meta or {}).get("source", "Unknown")
            snippet = (doc or "").strip()
            if snippet:
                snippets.append(RetrievedSnippet(source=source, snippet=snippet))
        
        return snippets


retrieval_service = RetrievalService()

