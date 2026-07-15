"""
ingest.py — read catalog.json and turn each dataset into ONE searchable text blob.

Why: the vector store searches over text. For each dataset we mash its English +
Arabic titles, descriptions, and column names into a single string. Because we
include both languages, a question in EITHER language can match the same dataset.
That is the whole trick behind the bilingual retrieval.
"""
import json
from config import settings


def load_catalog():
    """Return the list of dataset records from catalog.json."""
    with open(settings.CATALOG_PATH, encoding="utf-8") as f:
        data = json.load(f)
    return data["datasets"]


def dataset_to_document(ds):
    """Flatten one dataset record into a single string we can embed."""
    columns = ", ".join(ds.get("columns", []))
    # Put both languages in the same blob so either can match at search time.
    parts = [
        ds.get("title_en", ""),
        ds.get("title_ar", ""),
        ds.get("description_en", ""),
        ds.get("description_ar", ""),
        f"Columns: {columns}" if columns else "",
        f"Source: {ds.get('source_org', '')}",
    ]
    return "\n".join(p for p in parts if p)


def build_documents():
    """
    Return three parallel lists Chroma wants: ids, documents, metadatas.
    Keeping them parallel (same order, same length) is what Chroma expects.
    """
    ids, documents, metadatas = [], [], []
    for ds in load_catalog():
        ids.append(ds["id"])
        documents.append(dataset_to_document(ds))
        # Metadata travels with each vector so we can recover the source + file later.
        # 'id' is needed to measure routing accuracy in eval (did we pick the right
        # dataset?), and 'sample_data' lets the UI flag synthetic demo figures.
        metadatas.append({
            "id": ds["id"],
            "title_en": ds.get("title_en", ""),
            "title_ar": ds.get("title_ar", ""),
            "source_url": ds.get("source_url", ""),
            "source_org": ds.get("source_org", ""),
            "file": ds.get("file", ""),
            "content_type": ds.get("content_type", "descriptive"),
            "sample_data": bool(ds.get("sample_data", False)),
        })
    return ids, documents, metadatas


if __name__ == "__main__":
    # Quick sanity check: python -m src.ingest
    ids, docs, _ = build_documents()
    print(f"Loaded {len(ids)} datasets from the catalog:")
    for i, d in zip(ids, docs):
        print(f"\n--- {i} ---\n{d}")
