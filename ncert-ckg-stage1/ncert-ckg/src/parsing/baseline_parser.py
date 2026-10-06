"""A simple, layout-preserving PDF-to-DocumentBlock baseline parser.

This parser intentionally does not infer mathematical meaning. It records
native PDF text and embedded images so later parsers can be compared against a
small, reproducible baseline.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import pymupdf

from schemas.document_block import DocumentBlock


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
OUTPUT_DIR = PROJECT_ROOT / "data" / "document_blocks"

SECTION_PATTERN = re.compile(r"^\d+(?:\.\d+)+\s+.+")
SUBSECTION_PATTERN = re.compile(r"^\d+(?:\.\d+){2,}\s+.+")
FORMULA_MARKERS = re.compile(r"[=+−÷×*/∑∏√^]|\b(?:sin|cos|tan|log)\b", re.IGNORECASE)


def document_id_for(pdf_path: Path) -> str:
    return f"NCERT_X_MATH_{pdf_path.stem.upper()}"


def classify_text(text: str, bbox: list[float], page_height: float) -> str:
    """Apply transparent layout heuristics, keeping uncertain content as prose."""
    normalized = " ".join(text.split())
    y1, y2 = bbox[1], bbox[3]

    if y1 < page_height * 0.14:
        return "header"
    if y2 > page_height * 0.94:
        return "footer"
    if SUBSECTION_PATTERN.match(normalized):
        return "subsection_heading"
    if SECTION_PATTERN.match(normalized):
        return "section_heading"
    if len(normalized) < 100 and FORMULA_MARKERS.search(normalized):
        return "formula"
    return "paragraph"


def rounded_bbox(rect: pymupdf.Rect) -> list[float]:
    return [round(value, 2) for value in (rect.x0, rect.y0, rect.x1, rect.y1)]


def extract_page(pdf_path: Path, page_number: int, output_dir: Path) -> list[DocumentBlock]:
    """Extract text blocks and embedded images from one one-based PDF page."""
    document_id = document_id_for(pdf_path)
    with pymupdf.open(pdf_path) as document:
        page = document[page_number - 1]
        page_height = page.rect.height
        extracted: list[tuple[pymupdf.Rect, str, str | None]] = []

        for block in page.get_text("blocks", sort=True):
            rect = pymupdf.Rect(block[:4])
            text = block[4].strip()
            if text:
                extracted.append((rect, text, None))

        image_dir = output_dir / "images"
        for image_index, image in enumerate(page.get_images(full=True), start=1):
            xref = image[0]
            image_bytes = document.extract_image(xref)
            extension = image_bytes["ext"]
            image_name = f"page_{page_number:03d}_image_{image_index:02d}.{extension}"
            image_path = image_dir / image_name
            image_dir.mkdir(parents=True, exist_ok=True)
            image_path.write_bytes(image_bytes["image"])
            for rect in page.get_image_rects(xref):
                extracted.append((rect, "", str(Path("images") / image_name)))

    extracted.sort(key=lambda item: (round(item[0].y0, 1), round(item[0].x0, 1)))
    blocks: list[DocumentBlock] = []
    for reading_order, (rect, text, image_ref) in enumerate(extracted, start=1):
        block_type = "figure" if image_ref else classify_text(text, rounded_bbox(rect), page_height)
        blocks.append(
            DocumentBlock(
                document_id=document_id,
                page=page_number,
                block_id=f"{pdf_path.stem}_p{page_number:03d}_b{reading_order:02d}",
                type=block_type,
                bbox=rounded_bbox(rect),
                reading_order=reading_order,
                text=text or None,
                image_ref=image_ref,
                confidence=0.95 if image_ref else 1.0,
            )
        )
    return blocks


def write_page(pdf_path: Path, page_number: int, output_root: Path = OUTPUT_DIR) -> Path:
    """Write a page's blocks as JSON and return its path."""
    output_dir = output_root / pdf_path.stem
    blocks = extract_page(pdf_path, page_number, output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    destination = output_dir / f"page_{page_number:03d}.json"
    destination.write_text(
        json.dumps([block.to_dict() for block in blocks], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return destination


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract native PDF blocks into DocumentBlocks.")
    parser.add_argument("pdf", type=Path, help="PDF filename in data/raw, or a PDF path")
    parser.add_argument("--page", type=int, required=True, help="One-based PDF page number")
    args = parser.parse_args()

    pdf_path = args.pdf if args.pdf.is_absolute() else RAW_DIR / args.pdf
    if not pdf_path.is_file():
        parser.error(f"PDF not found: {pdf_path}")
    with pymupdf.open(pdf_path) as document:
        if not 1 <= args.page <= len(document):
            parser.error(f"--page must be between 1 and {len(document)}")

    print(write_page(pdf_path, args.page))


if __name__ == "__main__":
    main()
