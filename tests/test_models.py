from context_engine.models import Chunk, ChunkType, NodeType, EdgeType, GraphNode, GraphEdge, ConfidenceLevel


def test_chunk_creation():
    chunk = Chunk(
        id="abc123",
        content="def hello(): pass",
        chunk_type=ChunkType.FUNCTION,
        file_path="src/main.py",
        start_line=1,
        end_line=1,
        language="python",
        metadata={"git_author": "fazle"},
    )
    assert chunk.id == "abc123"
    assert chunk.chunk_type == ChunkType.FUNCTION
    assert chunk.embedding is None


def test_chunk_with_embedding():
    chunk = Chunk(
        id="abc123",
        content="def hello(): pass",
        chunk_type=ChunkType.FUNCTION,
        file_path="src/main.py",
        start_line=1,
        end_line=1,
        language="python",
    )
    chunk.embedding = [0.1, 0.2, 0.3]
    assert chunk.embedding == [0.1, 0.2, 0.3]


def test_graph_node_creation():
    node = GraphNode(
        id="func_hello",
        node_type=NodeType.FUNCTION,
        name="hello",
        file_path="src/main.py",
        properties={"start_line": 1},
    )
    assert node.node_type == NodeType.FUNCTION


def test_graph_edge_creation():
    edge = GraphEdge(
        source_id="func_hello",
        target_id="func_world",
        edge_type=EdgeType.CALLS,
    )
    assert edge.edge_type == EdgeType.CALLS


def test_confidence_level_from_score():
    assert ConfidenceLevel.from_score(0.9) == ConfidenceLevel.HIGH
    assert ConfidenceLevel.from_score(0.6) == ConfidenceLevel.MEDIUM
    assert ConfidenceLevel.from_score(0.3) == ConfidenceLevel.LOW
