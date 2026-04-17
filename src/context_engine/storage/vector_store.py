"""LanceDB-backed vector store for chunk embeddings."""
from pathlib import Path

import lancedb
import pyarrow as pa

from context_engine.models import Chunk, ChunkType


TABLE_NAME = "chunks"


class VectorStore:
    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        self._db = lancedb.connect(db_path)
        self._table = None

    def _ensure_table(self, vector_dim: int) -> None:
        if self._table is not None:
            return
        try:
            self._table = self._db.open_table(TABLE_NAME)
        except Exception:
            schema = pa.schema([
                pa.field("id", pa.string()),
                pa.field("content", pa.string()),
                pa.field("chunk_type", pa.string()),
                pa.field("file_path", pa.string()),
                pa.field("start_line", pa.int32()),
                pa.field("end_line", pa.int32()),
                pa.field("language", pa.string()),
                pa.field("vector", pa.list_(pa.float32(), vector_dim)),
            ])
            self._table = self._db.create_table(TABLE_NAME, schema=schema)

    def _chunk_to_row(self, chunk: Chunk) -> dict:
        return {
            "id": chunk.id,
            "content": chunk.content,
            "chunk_type": chunk.chunk_type.value,
            "file_path": chunk.file_path,
            "start_line": chunk.start_line,
            "end_line": chunk.end_line,
            "language": chunk.language,
            "vector": chunk.embedding,
        }

    def _row_to_chunk(self, row: dict) -> Chunk:
        return Chunk(
            id=row["id"],
            content=row["content"],
            chunk_type=ChunkType(row["chunk_type"]),
            file_path=row["file_path"],
            start_line=row["start_line"],
            end_line=row["end_line"],
            language=row["language"],
            embedding=row.get("vector"),
        )

    async def ingest(self, chunks: list[Chunk]) -> None:
        if not chunks:
            return
        vector_dim = len(chunks[0].embedding)
        self._ensure_table(vector_dim)
        rows = [self._chunk_to_row(c) for c in chunks if c.embedding]
        self._table.add(rows)

    async def search(
        self,
        query_embedding: list[float],
        top_k: int = 10,
        filters: dict | None = None,
    ) -> list[Chunk]:
        if self._table is None:
            return []
        query = self._table.search(query_embedding).limit(top_k)
        if filters:
            where_clauses = []
            for key, value in filters.items():
                where_clauses.append(f"{key} = '{value}'")
            query = query.where(" AND ".join(where_clauses))
        results = query.to_list()
        return [self._row_to_chunk(row) for row in results]

    async def delete_by_file(self, file_path: str) -> None:
        if self._table is None:
            return
        self._table.delete(f"file_path = '{file_path}'")

    async def get_by_id(self, chunk_id: str) -> Chunk | None:
        if self._table is None:
            return None
        results = self._table.search().where(f"id = '{chunk_id}'").limit(1).to_list()
        if not results:
            return None
        return self._row_to_chunk(results[0])
