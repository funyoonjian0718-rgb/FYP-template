import glob
import os
import uuid

# Disable ChromaDB telemetry completely
os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")

import chromadb
from chromadb.config import Settings

from app.core.settings import settings
from app.rag.embedding import EmbeddingService


def _chunk_text(text: str, *, chunk_size: int = 700, overlap: int = 120) -> list[str]:
    text = text.replace("\r\n", "\n").strip()
    if not text:
        return []
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(len(text), start + chunk_size)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == len(text):
            break
        start = max(0, end - overlap)
    return chunks


def main() -> None:
    os.makedirs(settings.chroma_dir, exist_ok=True)
    emb = EmbeddingService()
    # Use settings with telemetry disabled
    client = chromadb.PersistentClient(
        path=settings.chroma_dir,
        settings=Settings(anonymized_telemetry=False)
    )
    col = client.get_or_create_collection(name="fyp_kb", metadata={"hnsw:space": "cosine"})

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data"))
    paths = glob.glob(os.path.join(base_dir, "*.md")) + glob.glob(os.path.join(base_dir, "*.txt"))
    if not paths:
        raise RuntimeError(f"No knowledge base files found in {base_dir}")

    documents: list[str] = []
    metadatas: list[dict] = []
    ids: list[str] = []

    for p in paths:
        with open(p, "r", encoding="utf-8") as f:
            raw = f.read()
        for chunk in _chunk_text(raw):
            documents.append(chunk)
            metadatas.append({"source": os.path.basename(p)})
            ids.append(str(uuid.uuid4()))

    embeddings = emb.embed(documents)
    col.add(ids=ids, documents=documents, metadatas=metadatas, embeddings=embeddings)
    print(f"Ingested {len(documents)} chunks into {settings.chroma_dir}")


if __name__ == "__main__":
    main()

