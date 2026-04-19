"""Embedding generation using fastembed (lightweight ONNX-based embeddings).

Replaces the previous torch+transformers+optimum stack (~500MB) with
fastembed (~50MB). Same model (all-MiniLM-L6-v2), same quality, 10x
smaller install, no HuggingFace rate limits.
"""
import logging
from functools import lru_cache

import numpy as np
from fastembed import TextEmbedding

from context_engine.models import Chunk

log = logging.getLogger(__name__)

_DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


class Embedder:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        self._model_name = model_name
        resolved = f"sentence-transformers/{model_name}" if "/" not in model_name else model_name
        try:
            self._model = TextEmbedding(resolved)
        except Exception as exc:
            raise RuntimeError(
                f"Failed to load embedding model '{model_name}'. "
                f"Ensure fastembed is installed and the model name is valid. "
                f"Supported models: TextEmbedding.list_supported_models(). "
                f"Original error: {exc}"
            ) from exc

    def embed(self, chunks: list[Chunk], batch_size: int = 32) -> None:
        """Embed chunks in-place, setting chunk.embedding for each."""
        if not chunks:
            return
        texts = [c.content for c in chunks]
        embeddings = list(self._model.embed(texts, batch_size=batch_size))
        for chunk, emb in zip(chunks, embeddings):
            chunk.embedding = emb.tolist()

    @lru_cache(maxsize=256)
    def embed_query(self, query: str) -> tuple:
        """Embed a single query string. Returns tuple for LRU cache hashability.

        Callers that need a list (e.g. LanceDB) should use list(result)
        or the _to_list() helper in vector_store.
        """
        results = list(self._model.query_embed(query))
        return tuple(results[0].tolist())
