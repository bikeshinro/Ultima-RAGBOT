import os
import sys

# Ensure project root is on sys.path so `src` is importable when running
# this script directly (e.g. `python scripts/init_qdrant.py`).
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.db.qdrant import ensure_collection
from src.config import settings
from src.llm.embeddings import get_embeddings

model = get_embeddings(settings.LLM_PROVIDER, settings.EMBEDDING_MODEL)
ensure_collection(settings.QDRANT_COLLECTION, vector_size=model.dim())
print("Qdrant collection ready.")
