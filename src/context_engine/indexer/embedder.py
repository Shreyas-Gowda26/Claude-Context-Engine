"""Embedding generation using sentence-transformers."""
from sentence_transformers import SentenceTransformer
from context_engine.models import Chunk


class Embedder:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        self._model = SentenceTransformer(model_name)

    def embed(self, chunks: list[Chunk]) -> None:
        if not chunks:
            return
        texts = [c.content for c in chunks]
        embeddings = self._model.encode(texts, show_progress_bar=False)
        for chunk, emb in zip(chunks, embeddings):
            chunk.embedding = emb.tolist()

    def embed_query(self, query: str) -> list[float]:
        return self._model.encode(query, show_progress_bar=False).tolist()
