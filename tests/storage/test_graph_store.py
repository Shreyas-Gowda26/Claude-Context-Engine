import pytest

from context_engine.models import GraphNode, GraphEdge, NodeType, EdgeType
from context_engine.storage.graph_store import GraphStore


@pytest.fixture
def store(tmp_path):
    return GraphStore(db_path=str(tmp_path / "graph"))


@pytest.fixture
def sample_nodes():
    return [
        GraphNode(id="file_math", node_type=NodeType.FILE, name="math.py", file_path="math.py"),
        GraphNode(id="func_add", node_type=NodeType.FUNCTION, name="add", file_path="math.py"),
        GraphNode(id="func_sub", node_type=NodeType.FUNCTION, name="subtract", file_path="math.py"),
    ]


@pytest.fixture
def sample_edges():
    return [
        GraphEdge(source_id="file_math", target_id="func_add", edge_type=EdgeType.DEFINES),
        GraphEdge(source_id="file_math", target_id="func_sub", edge_type=EdgeType.DEFINES),
        GraphEdge(source_id="func_add", target_id="func_sub", edge_type=EdgeType.CALLS),
    ]


@pytest.mark.asyncio
async def test_ingest_nodes_and_edges(store, sample_nodes, sample_edges):
    # GraphStore is a no-op; ingest completes without error
    await store.ingest(sample_nodes, sample_edges)
    nodes = await store.get_nodes_by_file("math.py")
    assert nodes == []


@pytest.mark.asyncio
async def test_get_neighbors(store, sample_nodes, sample_edges):
    await store.ingest(sample_nodes, sample_edges)
    neighbors = await store.get_neighbors("func_add", edge_type=EdgeType.CALLS)
    assert neighbors == []


@pytest.mark.asyncio
async def test_get_nodes_by_type(store, sample_nodes, sample_edges):
    await store.ingest(sample_nodes, sample_edges)
    functions = await store.get_nodes_by_type(NodeType.FUNCTION)
    assert functions == []


@pytest.mark.asyncio
async def test_delete_by_file(store, sample_nodes, sample_edges):
    await store.ingest(sample_nodes, sample_edges)
    await store.delete_by_file("math.py")
    nodes = await store.get_nodes_by_file("math.py")
    assert nodes == []
