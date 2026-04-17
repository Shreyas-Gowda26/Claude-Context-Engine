"""Hybrid retrieval — vector search + graph traversal + confidence scoring."""
from context_engine.models import Chunk, ConfidenceLevel
from context_engine.storage.backend import StorageBackend
from context_engine.indexer.embedder import Embedder
from context_engine.retrieval.confidence import ConfidenceScorer
from context_engine.retrieval.query_parser import QueryParser, QueryIntent


class HybridRetriever:
    def __init__(self, backend: StorageBackend, embedder: Embedder) -> None:
        self._backend = backend
        self._embedder = embedder
        self._scorer = ConfidenceScorer()
        self._parser = QueryParser()

    async def retrieve(self, query: str, top_k: int = 10, confidence_threshold: float = 0.0) -> list[Chunk]:
        parsed = self._parser.parse(query)
        query_embedding = self._embedder.embed_query(query)

        vector_results = await self._backend.vector_search(
            query_embedding=query_embedding, top_k=top_k * 2,
        )

        scored = []
        for chunk in vector_results:
            idx = vector_results.index(chunk)
            approx_distance = idx / max(len(vector_results), 1)
            graph_hops = await self._estimate_graph_hops(chunk, parsed)
            score = self._scorer.score(chunk, vector_distance=approx_distance, graph_hops=graph_hops)
            chunk.confidence_score = score
            if score >= confidence_threshold:
                scored.append((chunk, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return [chunk for chunk, _ in scored[:top_k]]

    async def _estimate_graph_hops(self, chunk, parsed):
        if parsed.file_hints:
            for hint in parsed.file_hints:
                if hint in chunk.file_path:
                    return 0
        for keyword in parsed.keywords:
            if keyword.lower() in chunk.content.lower():
                return 0
        return 2
