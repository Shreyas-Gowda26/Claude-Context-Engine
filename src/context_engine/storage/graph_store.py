"""Graph store — no-op implementation (graph DB removed to keep install lightweight)."""

from context_engine.models import GraphNode, GraphEdge, NodeType, EdgeType


class GraphStore:
    def __init__(self, db_path: str) -> None:
        pass

    async def ingest(self, nodes: list[GraphNode], edges: list[GraphEdge]) -> None:
        pass

    async def get_neighbors(self, node_id: str, edge_type: EdgeType | None = None) -> list[GraphNode]:
        return []

    async def get_nodes_by_file(self, file_path: str) -> list[GraphNode]:
        return []

    async def get_nodes_by_type(self, node_type: NodeType) -> list[GraphNode]:
        return []

    async def delete_by_file(self, file_path: str) -> None:
        pass
