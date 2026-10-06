"""Serializable graph records with provenance carried on every semantic claim."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal


NodeType = Literal[
    "Curriculum", "Book", "Chapter", "Section", "Concept", "Definition",
    "Skill", "Formula", "Theorem", "Proof", "Example", "Exercise",
    "LearningOutcome", "Misconception", "Representation", "DocumentBlock", "Page",
]


@dataclass
class GraphNode:
    id: str
    type: NodeType
    name: str
    properties: dict[str, Any] = field(default_factory=dict)
    evidence_block_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class GraphEdge:
    source_id: str
    target_id: str
    type: str
    evidence_block_ids: list[str]
    inference_method: str
    confidence: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


SEMANTIC_NODE_TYPES = {
    "Concept", "Definition", "Skill", "Formula", "Theorem", "Proof", "Example",
    "Exercise", "LearningOutcome", "Misconception", "Representation",
}
