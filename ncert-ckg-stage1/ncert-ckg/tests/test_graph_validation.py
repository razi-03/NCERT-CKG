import unittest

from graph_validation.validate_graph import validate_graph
from schemas.knowledge_graph import GraphEdge, GraphNode


class GraphValidationTests(unittest.TestCase):
    def test_rejects_cyclic_prerequisites(self) -> None:
        nodes = [
            GraphNode("block:b1", "DocumentBlock", "b1"),
            GraphNode("concept:a", "Concept", "A", evidence_block_ids=["b1"]),
            GraphNode("concept:b", "Concept", "B", evidence_block_ids=["b1"]),
        ]
        edges = [
            GraphEdge("concept:a", "concept:b", "prerequisite_for", ["b1"], "manual", 1.0),
            GraphEdge("concept:b", "concept:a", "prerequisite_for", ["b1"], "manual", 1.0),
        ]

        self.assertIn("prerequisite_for relationships contain a cycle", validate_graph(nodes, edges))

    def test_rejects_semantic_node_without_evidence(self) -> None:
        errors = validate_graph([GraphNode("concept:a", "Concept", "A")], [])

        self.assertIn("concept:a (Concept) has no evidence", errors)


if __name__ == "__main__":
    unittest.main()
