"""
config.py — every setting you might want to tweak lives here, in one place.
Import this anywhere with:  from config import settings
"""
from pathlib import Path
import os
from dotenv import load_dotenv

# Load a local .env file if you have one (copy .env.example -> .env).
load_dotenv()

# Project root = the folder this file sits in. Everything is relative to it,
# so the project works no matter where you clone it.
ROOT = Path(__file__).resolve().parent


class Settings:
    # --- Where things live on disk ---
    RAW_DATA_DIR = ROOT / "data" / "raw"          # downloaded CSV/JSON datasets
    CATALOG_PATH = ROOT / "data" / "catalog.json"  # the metadata index you curate
    VECTOR_DIR = ROOT / "data" / "chroma"          # where Chroma persists embeddings

    # --- Embedding model (must be MULTILINGUAL for Arabic + English) ---
    # e5 models expect "query: ..." / "passage: ..." prefixes — handled in embed_store.py.
    EMBED_MODEL = os.getenv("EMBED_MODEL", "intfloat/multilingual-e5-large")

    # --- Ollama (local LLM) ---
    OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
    # A model good at instruction-following in both English and Arabic. Pull it with:
    #   ollama pull qwen2.5:7b
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")

    # --- Retrieval behaviour ---
    TOP_K = int(os.getenv("TOP_K", "3"))  # how many datasets to retrieve per question


settings = Settings()
