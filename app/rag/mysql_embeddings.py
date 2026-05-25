"""MySQL-based embedding storage and retrieval (replaces Chroma)."""
from __future__ import annotations

import json
import uuid

import numpy as np
from sqlalchemy import select

from app.core.settings import settings
from app.db.models_embeddings import Embedding
from app.db.session import SessionLocal
from app.rag.embedding import EmbeddingService
from app.rag.types import RetrievedSnippet


class MySQLEmbeddingService:
    """Store and retrieve embeddings from MySQL instead of Chroma."""

    def __init__(self):
        self.embedding_service = EmbeddingService()

    def add_chunks(self, documents: list[str], metadatas: list[dict], ids: list[str] | None = None) -> None:
        """Add document chunks and their embeddings to MySQL."""
        if not documents:
            return

        if ids is None:
            ids = [str(uuid.uuid4()) for _ in documents]

        # Compute embeddings
        embeddings = self.embedding_service.embed(documents)

        # Store in MySQL
        session = SessionLocal()
        try:
            for doc, metadata, chunk_id, emb_vec in zip(documents, metadatas, ids, embeddings):
                # Check if already exists
                existing = session.query(Embedding).filter(Embedding.chunk_id == chunk_id).first()
                if existing:
                    continue

                # Store embedding as JSON
                emb_json = json.dumps(emb_vec.tolist() if hasattr(emb_vec, "tolist") else emb_vec)
                embedding_record = Embedding(
                    chunk_id=chunk_id,
                    source=metadata.get("source", "unknown"),
                    chunk_text=doc,
                    embedding=emb_json,
                )
                session.add(embedding_record)

            session.commit()
        finally:
            session.close()

    def query(self, query_text: str, k: int = 4) -> list[RetrievedSnippet]:
        """Retrieve top-k most similar chunks using cosine similarity."""
        # Embed the query
        query_embedding = self.embedding_service.embed([query_text])[0]
        query_vec = np.array(query_embedding)

        # Retrieve all embeddings from MySQL
        session = SessionLocal()
        try:
            all_embeddings = session.query(Embedding).all()
            if not all_embeddings:
                return []

            # Compute cosine similarities
            similarities = []
            for record in all_embeddings:
                doc_vec = np.array(json.loads(record.embedding))
                # Cosine similarity
                sim = np.dot(query_vec, doc_vec) / (np.linalg.norm(query_vec) * np.linalg.norm(doc_vec) + 1e-8)
                similarities.append((sim, record))

            # Sort by similarity and return top-k
            similarities.sort(key=lambda x: x[0], reverse=True)
            results = []
            for sim, rec in similarities[:k]:
                text = rec.chunk_text.strip().replace("\n", " ")
                if len(text) > 260:
                    text = text[:260].rstrip() + "…"
                results.append(RetrievedSnippet(source=rec.source, snippet=text))
            return results
        finally:
            session.close()

    def clear_all(self) -> None:
        """Delete all embeddings (for re-ingestion)."""
        session = SessionLocal()
        try:
            session.query(Embedding).delete()
            session.commit()
        finally:
            session.close()

    def count(self) -> int:
        """Return the number of stored embeddings."""
        session = SessionLocal()
        try:
            return session.query(Embedding).count()
        finally:
            session.close()
