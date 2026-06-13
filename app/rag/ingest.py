import glob
import json
import os
import uuid
import csv

import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer

from app.core.settings import settings


def _chunk_text(text: str, *, chunk_size: int = 700, overlap: int = 120) -> list[str]:
    """Split text into overlapping chunks."""
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


def _load_markdown_files(base_dir: str) -> list[tuple[str, str, str]]:
    """Load .md and .txt files. Returns list of (content, source, type)."""
    docs = []
    for pattern in ["*.md", "*.txt"]:
        for path in glob.glob(os.path.join(base_dir, pattern)):
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            source = os.path.basename(path)
            docs.append((content, source, "guideline"))
    return docs


def _load_foods_json(base_dir: str) -> list[tuple[str, str, str]]:
    """Convert foods.json into RAG-retrievable text chunks."""
    docs = []
    foods_path = os.path.join(base_dir, "foods.json")
    if not os.path.exists(foods_path):
        return docs
    
    with open(foods_path, "r", encoding="utf-8") as f:
        foods = json.load(f)
    
    for food in foods:
        # Convert each food item into readable text
        text_parts = []
        text_parts.append(f"Food: {food.get('name', 'Unknown')}")
        if food.get("category"):
            text_parts.append(f"Category: {food['category']}")
        if food.get("serving_size"):
            text_parts.append(f"Serving: {food['serving_size']}")
        if food.get("calories"):
            text_parts.append(f"Calories: {food['calories']} kcal")
        if food.get("carbohydrates_g"):
            text_parts.append(f"Carbohydrates: {food['carbohydrates_g']}g")
        if food.get("protein_g"):
            text_parts.append(f"Protein: {food['protein_g']}g")
        if food.get("fat_g"):
            text_parts.append(f"Fat: {food['fat_g']}g")
        if food.get("fibre_g"):
            text_parts.append(f"Fiber: {food['fibre_g']}g")
        if food.get("sugar_g"):
            text_parts.append(f"Sugar: {food['sugar_g']}g")
        if food.get("glycemic_index"):
            text_parts.append(f"Glycemic Index: {food['glycemic_index']}")
        if food.get("health_advice"):
            text_parts.append(f"Health Advice: {food['health_advice']}")
        if food.get("alternatives"):
            text_parts.append(f"Better Alternatives: {food['alternatives']}")
        if food.get("diabetes_suitable") is not None:
            suitable = "Yes" if food['diabetes_suitable'] else "Not suitable"
            text_parts.append(f"Suitable for Diabetes: {suitable}")
        
        # Convert to single text block
        text = "\n".join(text_parts)
        docs.append((text, "foods.json", "food"))
    
    return docs


def _load_csv_dataset(base_dir: str, max_rows: int = 5000) -> list[tuple[str, str, str]]:
    """Load CSV datasets (like USDA FoodData Central)."""
    docs = []
    for csv_path in glob.glob(os.path.join(base_dir, "*.csv")):
        source = os.path.basename(csv_path)
        try:
            with open(csv_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                row_count = 0
                for row in reader:
                    if row_count >= max_rows:
                        break
                    
                    # Convert CSV row to text (adapt based on your CSV columns)
                    text_parts = []
                    if "name" in row or "food_name" in row:
                        name = row.get("name") or row.get("food_name")
                        text_parts.append(f"Food: {name}")
                    
                    if "category" in row or "food_category" in row:
                        cat = row.get("category") or row.get("food_category")
                        if cat:
                            text_parts.append(f"Category: {cat}")
                    
                    # Add nutrition info if available
                    for col in ["calories", "energy", "protein", "fat", "carbohydrates", "fiber", "sugar"]:
                        if col in row and row[col]:
                            text_parts.append(f"{col.capitalize()}: {row[col]}")
                    
                    if text_parts:
                        text = "\n".join(text_parts)
                        docs.append((text, source, "dataset"))
                    
                    row_count += 1
        except Exception as e:
            print(f"Warning: Could not load CSV {csv_path}: {e}")
    
    return docs


def main() -> None:
    """Ingest all data sources into ChromaDB vectorstore."""
    os.makedirs(settings.vectorstore_dir, exist_ok=True)
    
    # Initialize embeddings and ChromaDB
    model = SentenceTransformer(settings.embedding_model)
    client = chromadb.PersistentClient(
        path=settings.vectorstore_dir,
        settings=ChromaSettings(anonymized_telemetry=False)
    )
    collection = client.get_or_create_collection(
        name="dietary_kb",
        metadata={"hnsw:space": "cosine"}
    )
    
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data"))
    
    # Load all document types
    all_docs = []
    
    # 1. Load guidelines (markdown/text)
    print("📖 Loading guidelines...")
    md_docs = _load_markdown_files(base_dir)
    all_docs.extend(md_docs)
    print(f"   Loaded {len(md_docs)} guideline document(s)")
    
    # 2. Load Malaysian foods (JSON)
    print("🍜 Loading Malaysian foods...")
    food_docs = _load_foods_json(base_dir)
    all_docs.extend(food_docs)
    print(f"   Loaded {len(food_docs)} food items")
    
    # 3. Load CSV datasets (USDA, etc.)
    print("📊 Loading CSV datasets...")
    csv_docs = _load_csv_dataset(base_dir, max_rows=5000)
    all_docs.extend(csv_docs)
    print(f"   Loaded {len(csv_docs)} dataset rows")
    
    # Chunk and embed all documents
    documents: list[str] = []
    metadatas: list[dict] = []
    ids: list[str] = []
    
    print("\n✂️ Chunking documents...")
    for content, source, doc_type in all_docs:
        chunks = _chunk_text(content)
        for chunk in chunks:
            documents.append(chunk)
            metadatas.append({
                "source": source,
                "type": doc_type
            })
            ids.append(str(uuid.uuid4()))
    
    # Embed and store
    print(f"\n🔀 Embedding {len(documents)} chunks...")
    embeddings = model.encode(documents, normalize_embeddings=True).tolist()
    
    print("💾 Storing in ChromaDB...")
    collection.add(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas
    )
    
    print(f"\n✅ Ingestion complete!")
    print(f"   Total chunks: {len(documents)}")
    print(f"   Guidelines: {len([m for m in metadatas if m['type'] == 'guideline'])}")
    print(f"   Foods: {len([m for m in metadatas if m['type'] == 'food'])}")
    print(f"   Datasets: {len([m for m in metadatas if m['type'] == 'dataset'])}")
    print(f"   Vectorstore: {settings.vectorstore_dir}")


if __name__ == "__main__":
    main()

