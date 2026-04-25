from __future__ import annotations

from sentence_transformers import SentenceTransformer

from app.core.settings import settings


class EmbeddingService:
    def __init__(self) -> None:
        self._model = SentenceTransformer(settings.embedding_model)

    def embed(self, texts: list[str]) -> list[list[float]]:
        # cosine space works best if we normalize
        return self._model.encode(texts, normalize_embeddings=True).tolist()

