# src/data/ingest.py
import uuid
import hashlib
import time
from typing import Iterable
from pathlib import Path

from src.data.chunkers import split_by_sentences
from src.llm.embeddings import get_embeddings
from src.db.qdrant import upsert_points, delete_by_filter
from src.config import settings
from src.data.loaders import load_any


# Initialize global embeddings backend
embeddings = get_embeddings(settings.LLM_PROVIDER, settings.EMBEDDING_MODEL)


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_chunks(text: str, doc_id: str) -> list[dict]:
    chunks = split_by_sentences(text)
    out = []

    for i, c in enumerate(chunks):
        out.append({
            "chunk_id": f"{doc_id}:{i}",
            "chunk_hash": _hash(c),
            "text": c,
        })

    return out


def ingest_chunks(
    doc_id: str,
    text: str,
    embeddings,
    source_name: str,
    user_id: str | None = None,
    mime_type: str | None = None
):
    chunks = build_chunks(text, doc_id)

    vectors = embeddings.embed_texts([c["text"] for c in chunks])
    ids = [str(uuid.uuid4()) for _ in chunks]
    now = int(time.time())

    payloads = [{
        "doc_id": doc_id,
        "chunk_id": c["chunk_id"],
        "chunk_hash": c["chunk_hash"],
        "text": c["text"],
        "source": source_name,
        "user_id": user_id,
        "mime_type": mime_type,
        "updated_at": now,
    } for c in chunks]

    upsert_points(settings.QDRANT_COLLECTION, ids, vectors, payloads)
    return len(chunks)


def reindex_if_changed(
    doc_id: str,
    text: str,
    source_name: str,
    user_id: str | None = None,
    mime_type: str | None = None
):
    """
    Detects changes by chunk hash and reindexes only when needed.
    """
    from src.db.qdrant import list_payloads_by_filter

    # new chunks
    new_chunks = build_chunks(text, doc_id)
    new_hashes = {c["chunk_id"]: c["chunk_hash"] for c in new_chunks}

    # existing hashes
    existing = list_payloads_by_filter(
        collection=settings.QDRANT_COLLECTION,
        must={"doc_id": doc_id, "user_id": user_id} if user_id else {"doc_id": doc_id}
    )
    old_hashes = {p["chunk_id"]: p.get("chunk_hash") for p in existing}

    # changed?
    changed = (
        len(old_hashes) != len(new_hashes)
        or any(old_hashes.get(k) != v for k, v in new_hashes.items())
    )

    if not changed:
        return 0

    # delete old
    delete_by_filter(
        collection=settings.QDRANT_COLLECTION,
        must={"doc_id": doc_id, "user_id": user_id} if user_id else {"doc_id": doc_id}
    )

    # re-ingest
    backend = get_embeddings(settings.LLM_PROVIDER, settings.EMBEDDING_MODEL)
    return ingest_chunks(doc_id, text, backend, source_name, user_id, mime_type)


# -------------------------------------------
# Utility for file ingestion
# -------------------------------------------
def doc_id_for(path: str, user_id: str | None) -> str:
    """
    Stable doc_id based on user + name + file size + mtime.
    """
    p = Path(path)
    base = f"{user_id or 'global'}::{p.name}::{p.stat().st_size}::{int(p.stat().st_mtime)}"
    return hashlib.sha256(base.encode()).hexdigest()


def ingest_file(path: str, user_id: str | None = None, source_name: str | None = None):
    text, mime = load_any(path)
    doc_id = doc_id_for(path, user_id)
    return reindex_if_changed(
        doc_id,
        text,
        source_name or Path(path).name,
        user_id=user_id,
        mime_type=mime
    )
