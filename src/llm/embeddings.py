# src/llm/embeddings.py
from typing import List
from src.config import settings
from openai import OpenAI


# ==============================
# Base Interface
# ==============================
class Embeddings:
    """Abstract embedding provider interface."""

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        raise NotImplementedError

    def dim(self) -> int:
        raise NotImplementedError


# ==============================
# SentenceTransformers Provider
# ==============================
class SentenceTransformersEmbeddings(Embeddings):
    def __init__(self, model_name: str):
        from sentence_transformers import SentenceTransformer

        self.model = SentenceTransformer(model_name)

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        # returns Python lists, not numpy arrays
        return self.model.encode(texts, convert_to_numpy=False).tolist()

    def dim(self) -> int:
        return self.model.get_sentence_embedding_dimension()


# ==============================
# OpenAI Provider (new API)
# ==============================
class OpenAIEmbeddings(Embeddings):
    """
    Wrapper around OpenAI >=1.0 embeddings API.
    """

    def __init__(self, model_name: str):
        self.client = OpenAI()
        self.model_name = model_name

        # Query model to determine dimension once
        # Most OpenAI embedding models document dimensionality, but we infer it.
        probe = self.client.embeddings.create(
            model=model_name,
            input=["dimension probe"]
        )
        self._dim = len(probe.data[0].embedding)

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        resp = self.client.embeddings.create(
            model=self.model_name,
            input=texts
        )
        return [d.embedding for d in resp.data]

    def dim(self) -> int:
        return self._dim


# ==============================
# Ollama Provider
# ==============================
class OllamaEmbeddings(Embeddings):
    """
    Uses /api/embeddings endpoint on local Ollama server.
    """

    def __init__(self, model_name: str, base_url: str = "http://localhost:11434"):
        import requests

        self.http = requests
        self.model_name = model_name
        self.base_url = base_url

        # Probe dimension dynamically
        r = self.http.post(
            f"{self.base_url}/api/embeddings",
            json={"model": model_name, "prompt": "dimension probe"}
        )
        r.raise_for_status()
        self._dim = len(r.json()["embedding"])

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        out = []
        for t in texts:
            r = self.http.post(
                f"{self.base_url}/api/embeddings",
                json={"model": self.model_name, "prompt": t}
            )
            r.raise_for_status()
            out.append(r.json()["embedding"])
        return out

    def dim(self) -> int:
        return self._dim


# ==============================
# Factory
# ==============================
def get_embeddings(provider: str | None = None, model_name: str | None = None) -> Embeddings:
    """
    Factory to get the correct embedding backend.
    Explicit args override settings.
    """

    provider = provider or settings.LLM_PROVIDER
    model_name = model_name or settings.EMBEDDING_MODEL

    if provider == "sentence-transformers":
        return SentenceTransformersEmbeddings(model_name)

    if provider == "openai":
        return OpenAIEmbeddings(model_name)

    if provider == "ollama":
        return OllamaEmbeddings(model_name)

    raise ValueError(f"Unknown embeddings provider: {provider}")
