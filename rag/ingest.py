
import json
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

# Project paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "data" / "clean_dataset.json"
VECTORSTORE_DIR = BASE_DIR / "vectorstore"

INDEX_PATH = VECTORSTORE_DIR / "gita_index.faiss"
METADATA_PATH = VECTORSTORE_DIR / "metadata.json"

MODEL_NAME = "all-MiniLM-L6-v2"


def main():
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Clean dataset not found: {DATA_PATH}\n"
            "Run rag/prepare_dataset.py first."
        )

    with open(DATA_PATH, "r", encoding="utf-8") as file:
        documents = json.load(file)

    # Ignore any empty text documents.
    documents = [
        doc for doc in documents
        if isinstance(doc.get("text"), str) and doc["text"].strip()
    ]

    if not documents:
        raise ValueError("No usable documents found in clean_dataset.json")

    texts = [doc["text"] for doc in documents]

    print(f"Loaded {len(documents)} documents.")
    print("Loading embedding model...")

    model = SentenceTransformer(MODEL_NAME)

    print("Generating embeddings...")
    embeddings = model.encode(
        texts,
        convert_to_numpy=True,
        show_progress_bar=True,
        normalize_embeddings=True
    )

    embeddings = np.asarray(embeddings, dtype=np.float32)

    print("Embedding shape:", embeddings.shape)

    # Inner product on normalized vectors is cosine similarity.
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings)

    VECTORSTORE_DIR.mkdir(parents=True, exist_ok=True)

    faiss.write_index(index, str(INDEX_PATH))

    with open(METADATA_PATH, "w", encoding="utf-8") as file:
        json.dump(documents, file, ensure_ascii=False, indent=2)

    print("\nFAISS index created successfully!")
    print(f"Vectors stored: {index.ntotal}")
    print(f"Index: {INDEX_PATH}")
    print(f"Metadata: {METADATA_PATH}")


if __name__ == "__main__":
    main()
