from qdrant_client import QdrantClient, models
from qdrant_client.http.models import Filter, FieldCondition, MatchValue
from src.config import settings

_api_key = (settings.QDRANT_API_KEY or "").strip() or None
client = QdrantClient(url=settings.QDRANT_URL, api_key=_api_key)

def ensure_collection(name: str, vector_size: int = 1536):
    if name not in [c.name for c in client.get_collections().collections]:
        client.create_collection(
            collection_name=name,
            vectors_config=models.VectorParams(size=vector_size, distance=models.Distance.COSINE),
        )

def upsert_points(collection: str, ids, vectors, payloads):
    client.upsert(collection_name=collection, points=models.Batch(ids=ids, vectors=vectors, payloads=payloads))

def _to_filter(filters: dict):
    """
    Convert your filters dictionary to a Qdrant Filter object.
    """
    if not filters:
        return None
    must_conditions = []
    for key, value in filters.items():
        must_conditions.append({
            "key": key,
            "match": {"value": value}
        })
    return Filter(must=must_conditions)

def delete_by_filter(collection: str, must: dict):
    client.delete(collection_name=collection, points_selector=models.FilterSelector(filter=_to_filter(must)))

def search(collection: str, vector, limit: int = 5, filters: dict | None = None):
    response = client.query_points(collection_name=collection, query=vector, limit=limit, query_filter=_to_filter(filters))
    return response.points

def list_payloads_by_filter(collection: str, must: dict) -> list[dict]:
    # Scroll is better for listing payloads
    res, _ = client.scroll(collection_name=collection, scroll_filter=_to_filter(must), with_payload=True, limit=10000)
    return [p.payload for p in res]