"""
embed_store.py — the semantic-search layer.

Two jobs:
  1. build_index()  : embed every catalog document once and save to disk.
  2. search(query)  : embed the user's question and return the closest datasets.

We use a MULTILINGUAL e5 model. e5 models are trained to expect little prefixes:
  - documents you store  -> "passage: <text>"
  - questions you search -> "query: <text>"
Getting those prefixes right noticeably improves results, so we add them here.
"""
import chromadb
from sentence_transformers import SentenceTransformer

from config import settings
from src.ingest import build_documents

# Load the embedding model once at import time (it's a few hundred MB, so we
# don't want to reload it on every call).
_model = SentenceTransformer(settings.EMBED_MODEL)


def _embed(texts, kind):
    """kind is 'passage' (stored docs) or 'query' (user questions)."""
    prefixed = [f"{kind}: {t}" for t in texts]
    # normalize_embeddings=True lets us use cosine similarity cleanly.
    return _model.encode(prefixed, normalize_embeddings=True).tolist()


def _collection():
    """Open (or create) the persistent Chroma collection on disk."""
    client = chromadb.PersistentClient(path=str(settings.VECTOR_DIR))
    return client.get_or_create_collection("saudi_edu_datasets")


def build_index():
    """Embed the whole catalog and store it. Run this whenever the catalog changes."""
    ids, documents, metadatas = build_documents()
    embeddings = _embed(documents, kind="passage")

    col = _collection()
    # upsert = insert or overwrite, so re-running is safe and idempotent.
    col.upsert(ids=ids, documents=documents, metadatas=metadatas, embeddings=embeddings)
    print(f"Indexed {len(ids)} datasets into {settings.VECTOR_DIR}")


def search(query, top_k=None):
    """Return the top_k most relevant datasets for a question (either language)."""
    top_k = top_k or settings.TOP_K
    query_emb = _embed([query], kind="query")

    col = _collection()
    res = col.query(query_embeddings=query_emb, n_results=top_k)

    # Chroma returns nested lists (one per query); we only sent one query.
    hits = []
    for doc, meta, dist in zip(res["documents"][0], res["metadatas"][0], res["distances"][0]):
        hits.append({"document": doc, "metadata": meta, "distance": dist})
    return hits


if __name__ == "__main__":
    # Build the index, then run a quick bilingual smoke test.
    build_index()
    for q in ["How many schools are there per region?", "كم عدد المدارس في كل منطقة؟"]:
        print(f"\nQuery: {q}")
        for h in search(q):
            print(f"  -> {h['metadata']['title_en']}  (distance {h['distance']:.3f})")
