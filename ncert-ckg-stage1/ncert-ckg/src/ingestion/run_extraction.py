"""Generate baseline DocumentBlocks for semantic CKG source documents."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pymupdf

from parsing.baseline_parser import RAW_DIR, write_page


PROJECT_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = PROJECT_ROOT / "data" / "manifests" / "corpus_manifest.json"


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract all CKG-eligible corpus pages.")
    parser.add_argument("--limit-pages", type=int, help="Maximum pages per document, for a reproducible pilot.")
    args = parser.parse_args()
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    written = 0
    for record in manifest["documents"]:
        if record["source_role"] == "preliminary_material":
            continue
        path = RAW_DIR / record["filename"]
        with pymupdf.open(path) as document:
            page_count = min(len(document), args.limit_pages) if args.limit_pages else len(document)
        for page in range(1, page_count + 1):
            destination = PROJECT_ROOT / "data" / "document_blocks" / path.stem / f"page_{page:03d}.json"
            if destination.exists():
                continue
            write_page(path, page)
            written += 1
    print(f"Wrote {written} missing page-level DocumentBlock datasets.")


if __name__ == "__main__":
    main()
