"""Local storage backend — LanceDB vectors + SQLite FTS + SQLite graph."""
import asyncio
from pathlib import Path

from context_engine.models import Chunk, GraphNode, GraphEdge, EdgeType
from context_engine.storage.vector_store import VectorStore
from context_engine.storage.fts_store import FTSStore
from context_engine.storage.graph_store import GraphStore


class LocalBackend:
    def __init__(self, base_path: str) -> None:
        self._vector_store = VectorStore(db_path=str(Path(base_path) / "vectors"))
        self._fts_store = FTSStore(db_path=str(Path(base_path) / "fts"))
        self._graph_store = GraphStore(db_path=str(Path(base_path) / "graph"))

    async def ingest(
        self,
        chunks: list[Chunk],
        nodes: list[GraphNode],
        edges: list[GraphEdge],
    ) -> None:
        await asyncio.gather(
            self._vector_store.ingest(chunks),
            self._fts_store.ingest(chunks),
            self._graph_store.ingest(nodes, edges),
        )

    async def vector_search(
        self,
        query_embedding: list[float],
        top_k: int = 10,
        filters: dict | None = None,
    ) -> list[Chunk]:
        return await self._vector_store.search(query_embedding, top_k, filters)

    async def fts_search(
        self,
        query: str,
        top_k: int = 30,
    ) -> list[tuple[str, float]]:
        return await self._fts_store.search(query, top_k)

    async def graph_neighbors(
        self,
        node_id: str,
        edge_type: EdgeType | None = None,
    ) -> list[GraphNode]:
        return await self._graph_store.get_neighbors(node_id, edge_type)

    async def get_related_file_paths(self, file_paths: list[str]) -> list[str]:
        """Return file paths reachable via CALLS or IMPORTS edges from the given files.

        Used by the retriever for 1-hop graph expansion: if a result is in
        auth.py, also surface chunks from files that auth.py calls or imports.
        """
        from context_engine.models import EdgeType, NodeType

        input_set = set(file_paths)
        related: set[str] = set()

        for fp in file_paths:
            nodes = await self._graph_store.get_nodes_by_file(fp)
            for node in nodes:
                if node.node_type not in (NodeType.FUNCTION, NodeType.CLASS,
                                          NodeType.FILE, NodeType.MODULE):
                    continue
                for edge_type in (EdgeType.CALLS, EdgeType.IMPORTS):
                    neighbors = await self._graph_store.get_neighbors(
                        node.id, edge_type
                    )
                    for neighbor in neighbors:
                        if neighbor.file_path and neighbor.file_path not in input_set:
                            related.add(neighbor.file_path)

        return list(related)

    async def get_chunk_by_id(self, chunk_id: str) -> Chunk | None:
        return await self._vector_store.get_by_id(chunk_id)

    async def get_chunks_by_ids(self, chunk_ids: list[str]) -> list[Chunk]:
        return await self._vector_store.get_chunks_by_ids(chunk_ids)

    async def delete_by_file(self, file_path: str) -> None:
        await asyncio.gather(
            self._vector_store.delete_by_file(file_path),
            self._fts_store.delete_by_file(file_path),
            self._graph_store.delete_by_file(file_path),
        )

    def count_chunks(self) -> int:
        return self._vector_store.count()

    def file_chunk_counts(self) -> dict[str, int]:
        return self._vector_store.file_chunk_counts()

    async def clear(self) -> None:
        self._vector_store.clear()
        self._fts_store.clear()
        self._graph_store.clear()
