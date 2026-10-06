"""Deterministic checks that route unreliable extraction to review or reprocessing."""

from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class ExtractionFinding:
    document_id: str
    page: int
    block_id: str
    issue: str
    severity: str
    recommended_action: str
    notes: str


def validate_blocks(blocks: list[dict[str, object]]) -> list[ExtractionFinding]:
    findings: list[ExtractionFinding] = []
    for block in blocks:
        bbox = block["bbox"]
        text = str(block.get("text") or "")
        block_type = block["type"]
        if block_type == "figure" and (bbox[2] - bbox[0]) > 450 and (bbox[3] - bbox[1]) > 650:
            findings.append(ExtractionFinding(
                str(block["document_id"]), int(block["page"]), str(block["block_id"]),
                "FULL_PAGE_FIGURE", "MEDIUM", "MANUAL_REVIEW",
                "Likely decorative background; confirm it is not an instructional figure.",
            ))
        has_private_math_glyph = any(0xF000 <= ord(character) <= 0xF0FF for character in text)
        if has_private_math_glyph or (block_type == "formula" and len(text.replace(" ", "")) <= 3):
            findings.append(ExtractionFinding(
                str(block["document_id"]), int(block["page"]), str(block["block_id"]),
                "FORMULA_STRUCTURE_UNRELIABLE", "HIGH", "REPROCESS_WITH_MATH_OCR",
                "Native PDF text lost mathematical glyph, fraction, or operand structure.",
            ))
    return findings


def write_findings(findings: list[ExtractionFinding], destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=ExtractionFinding.__dataclass_fields__)
        writer.writeheader()
        writer.writerows(asdict(finding) for finding in findings)
