import pytest
from context_engine.models import Chunk, ChunkType
from context_engine.compression.compressor import Compressor

@pytest.fixture
def compressor():
    return Compressor(ollama_url="http://localhost:11434", model="phi3:mini")

@pytest.fixture
def sample_chunks():
    return [
        Chunk(id="c1", content="def add(a, b):\n    '''Add two numbers.'''\n    return a + b",
              chunk_type=ChunkType.FUNCTION, file_path="math.py",
              start_line=1, end_line=3, language="python", confidence_score=0.9),
        Chunk(id="c2", content="class Calculator:\n    pass",
              chunk_type=ChunkType.CLASS, file_path="calc.py",
              start_line=1, end_line=2, language="python", confidence_score=0.6),
    ]

@pytest.mark.asyncio
async def test_compress_without_ollama_falls_back(compressor, sample_chunks):
    results = await compressor.compress(sample_chunks, level="standard")
    assert len(results) > 0
    for chunk in results:
        assert chunk.compressed_content is not None

@pytest.mark.asyncio
async def test_compress_minimal_level(compressor, sample_chunks):
    results = await compressor.compress(sample_chunks, level="minimal")
    for chunk in results:
        assert len(chunk.compressed_content) <= len(chunk.content) + 50

@pytest.mark.asyncio
async def test_compress_preserves_original(compressor, sample_chunks):
    original_contents = [c.content for c in sample_chunks]
    await compressor.compress(sample_chunks, level="standard")
    for chunk, original in zip(sample_chunks, original_contents):
        assert chunk.content == original
