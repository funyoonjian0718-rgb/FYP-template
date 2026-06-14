from __future__ import annotations

import csv
import glob
import json
import os
import uuid
from typing import Any

import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer

from app.core.settings import settings


COLLECTION_NAME = "dietary_kb"
BATCH_SIZE = 128


def _chunk_text(text: str, *, chunk_size: int = 700, overlap: int = 120) -> list[str]:
    """Split long guideline text into overlapping chunks."""
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


def _clean_value(value: Any) -> str:
    """Convert CSV/JSON value to safe string."""
    if value is None:
        return ""

    text = str(value).strip()

    if text.lower() in {"none", "nan", "null"}:
        return ""

    return text


def _load_markdown_files(base_dir: str) -> list[tuple[str, dict]]:
    """
    Load .md and .txt guideline files.

    Important:
    Do NOT place developer guide files inside /data,
    because the chatbot may retrieve coding instructions instead of diet advice.
    """
    docs: list[tuple[str, dict]] = []

    ignored_names = {
        "RAG_fix_retrieval_prompt_and_ingestion_guide.md",
        "RAG_dataset_import_guide.md",
    }

    for pattern in ["*.md", "*.txt"]:
        for path in glob.glob(os.path.join(base_dir, pattern)):
            source = os.path.basename(path)

            if source in ignored_names:
                print(f"   Skipping developer guide: {source}")
                continue

            with open(path, "r", encoding="utf-8") as f:
                content = f.read().strip()

            if not content:
                continue

            metadata = {
                "source": source,
                "type": "guideline",
                "row_type": "guideline",
                "category": "",
                "food_name": "",
                "condition": "",
                "meal_time": "",
            }

            docs.append((content, metadata))

    return docs


def _load_foods_json(base_dir: str) -> list[tuple[str, dict]]:
    """
    Load foods.json if it exists.

    This is optional.
    For cleaner testing with the 10k KB, you can remove foods.json temporarily.
    """
    docs: list[tuple[str, dict]] = []

    foods_path = os.path.join(base_dir, "foods.json")

    if not os.path.exists(foods_path):
        return docs

    with open(foods_path, "r", encoding="utf-8") as f:
        foods = json.load(f)

    if not isinstance(foods, list):
        print("Warning: foods.json is not a list. Skipping.")
        return docs

    for food in foods:
        if not isinstance(food, dict):
            continue

        name = _clean_value(food.get("name"))
        category = _clean_value(food.get("category"))

        text_parts: list[str] = []

        if name:
            text_parts.append(f"Food: {name}")

        if category:
            text_parts.append(f"Category: {category}")

        field_map = [
            ("serving_size", "Serving size"),
            ("calories", "Calories"),
            ("carbohydrates_g", "Carbohydrates g"),
            ("protein_g", "Protein g"),
            ("fat_g", "Fat g"),
            ("fibre_g", "Fibre g"),
            ("fiber_g", "Fiber g"),
            ("sugar_g", "Sugar g"),
            ("sodium_mg", "Sodium mg"),
            ("potassium_mg", "Potassium mg"),
            ("phosphorus_mg", "Phosphorus mg"),
            ("iron_mg", "Iron mg"),
            ("glycemic_index", "Glycemic index"),
            ("health_advice", "Health advice"),
            ("alternatives", "Better alternatives"),
            ("price_myr", "Price MYR"),
        ]

        for key, label in field_map:
            value = _clean_value(food.get(key))
            if value:
                text_parts.append(f"{label}: {value}")

        diabetes_value = food.get("diabetes_suitable")
        if diabetes_value is not None:
            text_parts.append(f"Diabetes suitable: {diabetes_value}")

        text = "\n".join(text_parts).strip()

        if not text:
            continue

        metadata = {
            "source": "foods.json",
            "type": "food",
            "row_type": "food_item",
            "category": category,
            "food_name": name,
            "condition": "",
            "meal_time": "",
        }

        docs.append((text, metadata))

    return docs


def _csv_row_to_text(row: dict[str, str]) -> str:
    """
    Convert one CSV row into retrievable text.

    Best case:
    - If the CSV has rag_text, use that directly.

    Fallback:
    - Build readable text from nutrition columns.
    """
    rag_text = _clean_value(row.get("rag_text"))

    if rag_text:
        return rag_text

    text_parts: list[str] = []

    name = (
        _clean_value(row.get("name"))
        or _clean_value(row.get("food_name"))
        or _clean_value(row.get("Food"))
    )

    if name:
        text_parts.append(f"Food: {name}")

    category = (
        _clean_value(row.get("category"))
        or _clean_value(row.get("food_category"))
    )

    if category:
        text_parts.append(f"Category: {category}")

    field_map = [
        ("row_type", "Row type"),
        ("condition", "Condition"),
        ("meal_time", "Meal time"),
        ("serving_size", "Serving size"),
        ("calories", "Calories"),
        ("carbohydrates_g", "Carbohydrates g"),
        ("protein_g", "Protein g"),
        ("fat_g", "Fat g"),
        ("fibre_g", "Fibre g"),
        ("fiber_g", "Fiber g"),
        ("sugar_g", "Sugar g"),
        ("sodium_mg", "Sodium mg"),
        ("potassium_mg", "Potassium mg"),
        ("phosphorus_mg", "Phosphorus mg"),
        ("iron_mg", "Iron mg"),
        ("glycemic_index", "Glycemic index"),
        ("diabetes_suitable", "Diabetes suitable"),
        ("health_advice", "Health advice"),
        ("alternatives", "Alternatives"),
        ("price_myr", "Price MYR"),
        ("tags", "Tags"),
        ("advice", "Advice"),
        ("avoid", "Avoid"),
        ("recommended", "Recommended"),
    ]

    for key, label in field_map:
        value = _clean_value(row.get(key))
        if value:
            text_parts.append(f"{label}: {value}")

    return "\n".join(text_parts).strip()


def _load_csv_dataset(base_dir: str) -> list[tuple[str, dict]]:
    """
    Load all CSV files in /data.

    For your project, keep only:
    - malaysian_diet_rag_10000_multichunk_kb.csv

    Remove old CSV files from /data during testing to avoid duplicate/noisy retrieval.
    """
    docs: list[tuple[str, dict]] = []

    for csv_path in glob.glob(os.path.join(base_dir, "*.csv")):
        source = os.path.basename(csv_path)

        try:
            with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
                reader = csv.DictReader(f)

                row_count = 0

                for row in reader:
                    text = _csv_row_to_text(row)

                    if not text:
                        continue

                    metadata = {
                        "source": source,
                        "type": "dataset",
                        "row_type": _clean_value(row.get("row_type")),
                        "category": _clean_value(row.get("category")),
                        "food_name": (
                            _clean_value(row.get("name"))
                            or _clean_value(row.get("food_name"))
                        ),
                        "condition": _clean_value(row.get("condition")),
                        "meal_time": _clean_value(row.get("meal_time")),
                    }

                    docs.append((text, metadata))
                    row_count += 1

                print(f"   Loaded {row_count} rows from {source}")

        except Exception as e:
            print(f"Warning: Could not load CSV {csv_path}: {e}")

    return docs


def _prepare_documents(all_docs: list[tuple[str, dict]]) -> tuple[list[str], list[dict], list[str]]:
    """
    Prepare documents, metadata, and ids for ChromaDB.

    Dataset rows from the 10k CSV are already designed as RAG chunks,
    so we do not split them again.

    Guideline markdown can be long, so we split guideline text into chunks.
    """
    documents: list[str] = []
    metadatas: list[dict] = []
    ids: list[str] = []

    for content, metadata in all_docs:
        doc_type = metadata.get("type", "")

        if doc_type == "dataset":
            chunks = [content]
        else:
            chunks = _chunk_text(content)

        for chunk in chunks:
            documents.append(chunk)
            metadatas.append(metadata)
            ids.append(str(uuid.uuid4()))

    return documents, metadatas, ids


def _reset_collection(client: chromadb.PersistentClient):
    """
    Delete old Chroma collection and create a fresh one.

    This prevents duplicate old data from staying inside your vector database.
    """
    try:
        client.delete_collection(name=COLLECTION_NAME)
        print(f"🗑️ Deleted old collection: {COLLECTION_NAME}")
    except Exception:
        print(f"ℹ️ No old collection found: {COLLECTION_NAME}")

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    return collection


def _add_to_chroma_in_batches(
    *,
    collection,
    model: SentenceTransformer,
    documents: list[str],
    metadatas: list[dict],
    ids: list[str],
) -> None:
    """Embed and add documents to ChromaDB in batches."""
    total = len(documents)

    for start in range(0, total, BATCH_SIZE):
        end = min(start + BATCH_SIZE, total)

        batch_docs = documents[start:end]
        batch_metas = metadatas[start:end]
        batch_ids = ids[start:end]

        embeddings = model.encode(
            batch_docs,
            normalize_embeddings=True,
            show_progress_bar=False,
        ).tolist()

        collection.add(
            ids=batch_ids,
            documents=batch_docs,
            embeddings=embeddings,
            metadatas=batch_metas,
        )

        print(f"   Added {end}/{total} chunks")


def main() -> None:
    """Ingest all dietary knowledge base files into ChromaDB."""
    os.makedirs(settings.vectorstore_dir, exist_ok=True)

    base_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "data")
    )

    print(f"📁 Data folder: {base_dir}")
    print(f"📁 Vectorstore folder: {settings.vectorstore_dir}")

    if not os.path.exists(base_dir):
        raise FileNotFoundError(f"Data folder not found: {base_dir}")

    print("\n📖 Loading guideline files...")
    guideline_docs = _load_markdown_files(base_dir)
    print(f"   Loaded {len(guideline_docs)} guideline document(s)")

    print("\n🍜 Loading foods.json...")
    food_docs = _load_foods_json(base_dir)
    print(f"   Loaded {len(food_docs)} food item(s) from foods.json")

    print("\n📊 Loading CSV datasets...")
    csv_docs = _load_csv_dataset(base_dir)
    print(f"   Loaded {len(csv_docs)} CSV row(s) total")

    all_docs = []
    all_docs.extend(guideline_docs)
    all_docs.extend(food_docs)
    all_docs.extend(csv_docs)

    if not all_docs:
        raise RuntimeError("No documents found. Please add KB files into the data folder.")

    print("\n✂️ Preparing chunks...")
    documents, metadatas, ids = _prepare_documents(all_docs)

    print(f"   Total chunks prepared: {len(documents)}")

    guideline_count = sum(1 for m in metadatas if m.get("type") == "guideline")
    food_count = sum(1 for m in metadatas if m.get("type") == "food")
    dataset_count = sum(1 for m in metadatas if m.get("type") == "dataset")

    print(f"   Guideline chunks: {guideline_count}")
    print(f"   Food chunks: {food_count}")
    print(f"   Dataset chunks: {dataset_count}")

    print("\n🧠 Loading embedding model...")
    model = SentenceTransformer(settings.embedding_model)

    print("\n💾 Connecting to ChromaDB...")
    client = chromadb.PersistentClient(
        path=settings.vectorstore_dir,
        settings=ChromaSettings(anonymized_telemetry=False),
    )

    collection = _reset_collection(client)

    print("\n🔀 Embedding and storing chunks...")
    _add_to_chroma_in_batches(
        collection=collection,
        model=model,
        documents=documents,
        metadatas=metadatas,
        ids=ids,
    )

    print("\n✅ Ingestion complete!")
    print(f"   Collection: {COLLECTION_NAME}")
    print(f"   Total chunks stored: {collection.count()}")
    print(f"   Vectorstore: {settings.vectorstore_dir}")

    print("\nRecommended check:")
    print("   If you are using the 10k KB, dataset chunks should be around 10036.")
    print("   If dataset chunks show only 5000, you are still using the old ingest script.")
    print("   If dataset chunks are much higher, you probably still have old CSV files in /data.")


if __name__ == "__main__":
    main()