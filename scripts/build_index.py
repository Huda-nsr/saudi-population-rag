"""
build_index.py — run this once (and after every catalog change) to build the
vector store from data/catalog.json.

Usage from the project root:
    python scripts/build_index.py
"""
import sys
from pathlib import Path

# Make sure we can import the project modules when run as a script.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.embed_store import build_index

if __name__ == "__main__":
    build_index()
    print("Done. You can now run:  python app.py")
