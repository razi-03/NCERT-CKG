"""Validation rules that prevent unsupported or cyclic curriculum claims."""

from __future__ import annotations

from schemas.knowledge_graph import GraphEdge, GraphNode, SEMANTIC_NODE_TYPES


def validate_graph(nodes: list[GraphNode], edges: list[GraphEdge]) -> list[str]:
    errors: list[str] = []
    node_ids = {node.id for node in nodes}
    block_ids = {node.id.removeprefix("block:") for node in nodes if node.type == "DocumentBlock"}
    for node in nodes:
        if node.type in SEMANTIC_NODE_TYPES and not node.evidence_block_ids:
            errors.append(f"{node.id} ({node.type}) has no evidence")
        if any(block_id not in block_ids for block_id in node.evidence_block_ids):
            errors.append(f"{node.id} cites a missing DocumentBlock")
    for edge in edges:
        if edge.source_id not in node_ids or edge.target_id not in node_ids:
            errors.append(f"{edge.type} edge has a missing endpoint")
        if not 0.0 <= edge.confidence <= 1.0:
            errors.append(f"{edge.type} edge has invalid confidence")
        if edge.type not in {"contains", "evidenced_by"} and not edge.evidence_block_ids:
            errors.append(f"{edge.type} edge lacks evidence")

    adjacency: dict[str, list[str]] = {}
    for edge in edges:
        if edge.type == "prerequisite_for":
            adjacency.setdefault(edge.source_id, []).append(edge.target_id)
    visiting, visited = set(), set()
    def visit(node_id: str) -> bool:
        if node_id in visiting:
            return True
        if node_id in visited:
            return False
        visiting.add(node_id)
        cyclic = any(visit(target) for target in adjacency.get(node_id, []))
        visiting.remove(node_id)
        visited.add(node_id)
        return cyclic
    if any(visit(node_id) for node_id in adjacency):
        errors.append("prerequisite_for relationships contain a cycle")
    return errors
