import pytest
from context_engine.models import Chunk, ChunkType
from context_engine.indexer.embedder import Embedder


@pytest.fixture
def embedder():
    return Embedder(model_name="all-MiniLM-L6-v2")


@pytest.fixture
def sample_chunks():
    return [
        Chunk(id="c1", content="def add(a, b): return a + b",
              chunk_type=ChunkType.FUNCTION, file_path="math.py",
              start_line=1, end_line=1, language="python"),
        Chunk(id="c2", content="def subtract(a, b): return a - b",
              chunk_type=ChunkType.FUNCTION, file_path="math.py",
              start_line=3, end_line=3, language="python"),
    ]


def test_embed_chunks_adds_embeddings(embedder, sample_chunks):
    embedder.embed(sample_chunks)
    for chunk in sample_chunks:
        assert chunk.embedding is not None
        assert len(chunk.embedding) > 0
        assert isinstance(chunk.embedding[0], float)


def test_embed_query_returns_vector(embedder):
    vec = embedder.embed_query("find the add function")
    assert len(vec) > 0
    assert isinstance(vec[0], float)


def test_embedding_dimensions_match(embedder, sample_chunks):
    embedder.embed(sample_chunks)
    query_vec = embedder.embed_query("test")
    assert len(sample_chunks[0].embedding) == len(query_vec)
