"""Embedding providers used by ingestion and retrieval."""

from __future__ import annotations

import hashlib
import math
import os
import re
from typing import Protocol

from openai import OpenAI


DEFAULT_HASH_DIMENSIONS = 384
DEFAULT_SENTENCE_TRANSFORMERS_MODEL = "BAAI/bge-small-en-v1.5"
DEFAULT_OPENAI_MODEL = "text-embedding-3-small"


class EmbeddingClient(Protocol):
    """Small interface shared by local and hosted embedding providers."""

    provider_name: str
    model_name: str

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts."""

    def embed_query(self, query: str) -> list[float]:
        """Embed a single search query."""


class HashEmbeddingClient:
    """Dependency-free keyword embedding client for MVP wiring.

    This is not a production semantic embedding model. It is a deterministic
    bag-of-words hashing embedder that gives Chroma real vectors without model
    downloads, PyTorch installs, or API usage. It is good enough for testing the
    data -> chunk -> vector DB -> retrieve flow on this small corpus.
    """

    provider_name = "hash"

    def __init__(self, dimensions: int = DEFAULT_HASH_DIMENSIONS) -> None:
        if dimensions <= 0:
            raise ValueError("Hash embedding dimensions must be greater than 0.")
        self.dimensions = dimensions
        self.model_name = f"hashing-bow-{dimensions}"

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]

    def embed_query(self, query: str) -> list[float]:
        return self._embed(query)

    def _embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions

        for token in tokenize(text):
            digest = hashlib.sha1(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign

        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector

        return [value / norm for value in vector]


class SentenceTransformersEmbeddingClient:
    """Sentence Transformers embedding client for stronger local retrieval."""

    provider_name = "sentence-transformers"

    def __init__(self, model_name: str = DEFAULT_SENTENCE_TRANSFORMERS_MODEL) -> None:
        self.model_name = model_name
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RuntimeError(
                "sentence-transformers is required for this provider. "
                "Install dependencies with `pip install -r requirements.txt`."
            ) from exc

        self._model = SentenceTransformer(model_name)

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        embeddings = self._model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return embeddings.tolist()

    def embed_query(self, query: str) -> list[float]:
        return self.embed_texts([query])[0]


class OpenAIEmbeddingClient:
    """OpenAI embedding client for later quality comparisons."""

    provider_name = "openai"

    def __init__(self, api_key: str, model_name: str = DEFAULT_OPENAI_MODEL) -> None:
        self.model_name = model_name
        self._client = OpenAI(api_key=api_key)

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        response = self._client.embeddings.create(model=self.model_name, input=texts)
        return [item.embedding for item in response.data]

    def embed_query(self, query: str) -> list[float]:
        response = self._client.embeddings.create(model=self.model_name, input=query)
        return response.data[0].embedding


def create_embedding_client() -> EmbeddingClient:
    """Create the configured embedding client.

    EMBEDDING_PROVIDER defaults to hash so MVP development does not require
    model downloads or API tokens. Set EMBEDDING_PROVIDER=openai when you want
    hosted embeddings, or sentence-transformers when your local ML stack is
    ready.
    """
    provider = os.getenv("EMBEDDING_PROVIDER", "hash").strip().lower()

    if provider == "hash":
        dimensions = int(os.getenv("HASH_EMBEDDING_DIMENSIONS", str(DEFAULT_HASH_DIMENSIONS)))
        return HashEmbeddingClient(dimensions=dimensions)

    if provider in {"sentence-transformers", "local"}:
        model_name = os.getenv("LOCAL_EMBEDDING_MODEL", DEFAULT_SENTENCE_TRANSFORMERS_MODEL)
        return SentenceTransformersEmbeddingClient(model_name=model_name)

    if provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is required when EMBEDDING_PROVIDER=openai.")
        model_name = os.getenv("OPENAI_EMBEDDING_MODEL", DEFAULT_OPENAI_MODEL)
        return OpenAIEmbeddingClient(api_key=api_key, model_name=model_name)

    raise RuntimeError("EMBEDDING_PROVIDER must be 'hash', 'sentence-transformers', or 'openai'.")


def tokenize(text: str) -> list[str]:
    """Tokenize text for the dependency-free hash embedder."""
    return re.findall(r"[a-z0-9_]+", text.lower())
