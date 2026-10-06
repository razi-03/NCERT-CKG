"""Build a transparent, provenance-first CKG from extracted DocumentBlocks."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

from canonicalization.canonicalize import canonicalize, normalized_name
from graph_validation.validate_graph import validate_graph
from schemas.knowledge_graph import GraphEdge, GraphNode
from validation.extraction_validation import validate_blocks, write_findings


PROJECT_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = PROJECT_ROOT / "data" / "manifests" / "corpus_manifest.json"
BLOCKS_DIR = PROJECT_ROOT / "data" / "document_blocks"
GRAPH_PATH = PROJECT_ROOT / "data" / "ckg" / "ncert_x_mathematics.json"
REVIEW_PATH = PROJECT_ROOT / "evaluation" / "extraction_review_queue.csv"
SECTION_TITLE = re.compile(r"^\d+(?:\.\d+)+\s+(.+)$")
DEFINITION = re.compile(r"^(.{3,80}?)\s+is called\s+", re.IGNORECASE)


def stable_id(kind: str, value: str) -> str:
    digest = hashlib.sha1(value.encode("utf-8")).hexdigest()[:12]
    return f"{kind.lower()}:{digest}"


def load_blocks(document_stem: str) -> list[dict[str, object]]:
    blocks: list[dict[str, object]] = []
    for path in sorted((BLOCKS_DIR / document_stem).glob("page_*.json")):
        blocks.extend(json.loads(path.read_text(encoding="utf-8")))
    return blocks


def add_evidence_edge(edges: list[GraphEdge], node_id: str, block_id: str) -> None:
    edges.append(GraphEdge(node_id, f"block:{block_id}", "evidenced_by", [block_id], "source_block", 1.0))


def build_graph() -> tuple[list[GraphNode], list[GraphEdge], list[str], list[object]]:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    nodes = [
        GraphNode("curriculum:ncert-x-math", "Curriculum", "NCERT Class X Mathematics"),
        GraphNode("book:ncert-x-math", "Book", "NCERT Class X Mathematics Textbook"),
    ]
    edges = [GraphEdge("curriculum:ncert-x-math", "book:ncert-x-math", "contains", [], "manifest", 1.0)]
    findings: list[object] = []

    for document in manifest["documents"]:
        document_id, filename = document["document_id"], document["filename"]
        stem = Path(filename).stem
        role = document["source_role"]
        if role == "preliminary_material":
            nodes.append(GraphNode(f"chapter:{stem}", "Chapter", "Preliminary material", {
                "document_id": document_id, "semantic_extraction": False, "retained_as": "metadata_only",
            }))
            edges.append(GraphEdge("book:ncert-x-math", f"chapter:{stem}", "contains", [], "manifest", 1.0))
            continue

        chapter = GraphNode(f"chapter:{stem}", "Chapter", document["title"] or stem, {
            "document_id": document_id,
            "chapter_number": document["chapter_number"],
            "source_role": role,
            "is_additional": role == "additional_content",
            "is_answers": role == "answer_key",
        })
        nodes.append(chapter)
        edges.append(GraphEdge("book:ncert-x-math", chapter.id, "contains", [], "manifest", 1.0))
        blocks = load_blocks(stem)
        findings.extend(validate_blocks(blocks))
        current_section = chapter.id
        current_concept: str | None = None
        current_theorem: str | None = None

        for block in blocks:
            block_id = str(block["block_id"])
            page_id = f"page:{document_id}:{block['page']}"
            if not any(node.id == page_id for node in nodes):
                nodes.append(GraphNode(page_id, "Page", f"{filename} page {block['page']}", {
                    "document_id": document_id, "page": block["page"],
                }))
                edges.append(GraphEdge(chapter.id, page_id, "contains", [], "source_structure", 1.0))
            nodes.append(GraphNode(f"block:{block_id}", "DocumentBlock", block_id, {
                "type": block["type"], "bbox": block["bbox"], "text": block.get("text"),
                "latex": block.get("latex"), "image_ref": block.get("image_ref"),
                "confidence": block["confidence"],
            }))
            edges.append(GraphEdge(page_id, f"block:{block_id}", "contains", [], "source_structure", 1.0))
            text = " ".join(str(block.get("text") or "").split())
            match = SECTION_TITLE.match(text)
            if match:
                name = match.group(1)
                current_section = stable_id("section", f"{document_id}:{block_id}")
                nodes.append(GraphNode(current_section, "Section", name, {}, [block_id]))
                edges.append(GraphEdge(chapter.id, current_section, "contains", [block_id], "heading_pattern", 0.95))
                add_evidence_edge(edges, current_section, block_id)
                if name.lower() != "introduction":
                    concept_id = stable_id("concept", normalized_name(name))
                    nodes.append(GraphNode(concept_id, "Concept", name, {"extraction": "section_heading"}, [block_id]))
                    edges.append(GraphEdge(current_section, concept_id, "contains", [block_id], "heading_pattern", 0.9))
                    add_evidence_edge(edges, concept_id, block_id)
                    current_concept = concept_id
                else:
                    current_concept = None
                current_theorem = None
                continue

            if not text:
                continue
            semantic_type, relation = None, None
            if block["type"] == "formula":
                semantic_type, relation = "Formula", "has_formula"
            elif text.lower().startswith("theorem"):
                semantic_type, relation = "Theorem", "contains"
            elif text.lower().startswith("proof"):
                semantic_type, relation = "Proof", "contains"
            elif text.lower().startswith("example"):
                semantic_type, relation = "Example", "contains"
            elif text.lower().startswith(("exercise", "exercises")):
                semantic_type, relation = "Exercise", "contains"
            elif DEFINITION.match(text):
                semantic_type, relation = "Definition", "defined_by"
            if semantic_type:
                entity_id = stable_id(semantic_type, f"{document_id}:{block_id}")
                node = GraphNode(entity_id, semantic_type, text[:160], {"section_id": current_section}, [block_id])
                nodes.append(node)
                edges.append(GraphEdge(current_section, entity_id, "contains", [block_id], "rule_based_extraction", 0.8))
                add_evidence_edge(edges, entity_id, block_id)
                if relation == "has_formula":
                    edges.append(GraphEdge(current_concept or current_section, entity_id, relation, [block_id], "rule_based_extraction", 0.8))
                elif semantic_type == "Definition":
                    subject = DEFINITION.match(text).group(1)  # matched above
                    definition_concept = current_concept or stable_id("concept", normalized_name(subject))
                    if current_concept is None:
                        nodes.append(GraphNode(definition_concept, "Concept", subject, {"extraction": "definition_subject"}, [block_id]))
                        edges.append(GraphEdge(current_section, definition_concept, "contains", [block_id], "definition_pattern", 0.75))
                        add_evidence_edge(edges, definition_concept, block_id)
                    edges.append(GraphEdge(definition_concept, entity_id, relation, [block_id], "definition_pattern", 0.8))
                elif semantic_type == "Theorem":
                    current_theorem = entity_id
                    if current_concept:
                        edges.append(GraphEdge(entity_id, current_concept, "depends_on", [block_id], "same_section_context", 0.65))
                elif semantic_type == "Proof" and current_theorem:
                    edges.append(GraphEdge(entity_id, current_theorem, "uses", [block_id], "adjacent_theorem_context", 0.75))
                elif semantic_type in {"Example", "Exercise"} and current_concept:
                    edges.append(GraphEdge(entity_id, current_concept, "tests_concept", [block_id], "same_section_context", 0.65))

    nodes, aliases = canonicalize(nodes)
    for edge in edges:
        edge.source_id = aliases.get(edge.source_id, edge.source_id)
        edge.target_id = aliases.get(edge.target_id, edge.target_id)
    unique_edges = {(edge.source_id, edge.target_id, edge.type, tuple(edge.evidence_block_ids)): edge for edge in edges}
    edges = list(unique_edges.values())
    return nodes, edges, validate_graph(nodes, edges), findings


def main() -> None:
    parser = argparse.ArgumentParser(description="Build provenance-first CKG JSON from DocumentBlocks.")
    parser.add_argument("--output", type=Path, default=GRAPH_PATH)
    args = parser.parse_args()
    nodes, edges, errors, findings = build_graph()
    write_findings(findings, REVIEW_PATH)
    if errors:
        raise SystemExit("Graph validation failed:\n- " + "\n- ".join(errors))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({"nodes": [node.to_dict() for node in nodes], "edges": [edge.to_dict() for edge in edges]}, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {len(nodes)} nodes and {len(edges)} edges to {args.output}")
    print(f"Wrote {len(findings)} extraction review findings to {REVIEW_PATH}")


if __name__ == "__main__":
    main()
