import pytest

from context_engine.models import Chunk, ChunkType
from context_engine.storage.vector_store import VectorStore


@pytest.fixture
def store(tmp_path):
    return VectorStore(db_path=str(tmp_path / "vectors"))


@pytest.fixture
def sample_chunks():
    return [
        Chunk(
            id="chunk_1",
            content="def add(a, b): return a + b",
            chunk_type=ChunkType.FUNCTION,
            file_path="math.py",
            start_line=1,
            end_line=1,
            language="python",
            embedding=[0.1, 0.2, 0.3, 0.4],
        ),
        Chunk(
            id="chunk_2",
            content="def subtract(a, b): return a - b",
            chunk_type=ChunkType.FUNCTION,
            file_path="math.py",
            start_line=3,
            end_line=3,
            language="python",
            embedding=[0.5, 0.6, 0.7, 0.8],
        ),
    ]


@pytest.mark.asyncio
async def test_ingest_and_search(store, sample_chunks):
    await store.ingest(sample_chunks)
    results = await store.search(query_embedding=[0.1, 0.2, 0.3, 0.4], top_k=2)
    assert len(results) > 0
    assert results[0].id == "chunk_1"


@pytest.mark.asyncio
async def test_search_with_filter(store, sample_chunks):
    await store.ingest(sample_chunks)
    results = await store.search(
        query_embedding=[0.1, 0.2, 0.3, 0.4],
        top_k=2,
        filters={"language": "python"},
    )
    assert all(c.language == "python" for c in results)


@pytest.mark.asyncio
async def test_delete_by_file_path(store, sample_chunks):
    await store.ingest(sample_chunks)
    await store.delete_by_file(file_path="math.py")
    results = await store.search(query_embedding=[0.1, 0.2, 0.3, 0.4], top_k=10)
    assert len(results) == 0


@pytest.mark.asyncio
async def test_get_by_id(store, sample_chunks):
    await store.ingest(sample_chunks)
    chunk = await store.get_by_id("chunk_1")
    assert chunk is not None
    assert chunk.content == "def add(a, b): return a + b"
