import glob
import os
import uuid

from app.core.settings import settings
from app.rag.mysql_embeddings import MySQLEmbeddingService


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
    emb_service = MySQLEmbeddingService()
    
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

    # Store in MySQL instead of Chroma
    emb_service.add_chunks(documents, metadatas, ids)
    print(f"Ingested {len(documents)} chunks into MySQL embeddings table")


if __name__ == "__main__":
    main()


if __name__ == "__main__":
    main()

