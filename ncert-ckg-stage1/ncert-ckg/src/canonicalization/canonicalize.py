"""Conservative canonicalization: merge only exact normalized names of one type."""

from __future__ import annotations

import re

from schemas.knowledge_graph import GraphNode


def normalized_name(name: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", name.lower())).strip()


def canonicalize(nodes: list[GraphNode]) -> tuple[list[GraphNode], dict[str, str]]:
    canonical: dict[tuple[str, str], GraphNode] = {}
    aliases: dict[str, str] = {}
    for node in nodes:
        if node.type not in {"Concept", "Skill", "LearningOutcome", "Misconception", "Representation"}:
            aliases[node.id] = node.id
            canonical[(node.type, node.id)] = node
            continue
        key = (node.type, normalized_name(node.name))
        existing = canonical.get(key)
        if existing is None:
            canonical[key] = node
            aliases[node.id] = node.id
            continue
        aliases[node.id] = existing.id
        existing.evidence_block_ids = sorted(set(existing.evidence_block_ids + node.evidence_block_ids))
    return list(canonical.values()), aliases
