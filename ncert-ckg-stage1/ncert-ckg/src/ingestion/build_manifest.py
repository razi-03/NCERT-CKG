from __future__ import annotations

import json
import re
from pathlib import Path

import pymupdf


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW_DIR = PROJECT_ROOT / "data" / "raw"
MANIFEST_DIR = PROJECT_ROOT / "data" / "manifests"
MANIFEST_PATH = MANIFEST_DIR / "corpus_manifest.json"


# ============================================================
# EXPECTED NCERT FILES
# ============================================================

EXPECTED_FILES = [
    f"jemh1{chapter:02d}.pdf"
    for chapter in range(1, 15)
] + [
    "jemh1a1.pdf",
    "jemh1a2.pdf",
    "jemh1an.pdf",
    "jemh1ps.pdf",
]


# ============================================================
# DOCUMENT CLASSIFICATION
# ============================================================

def classify_document(filename: str) -> str:
    stem = Path(filename).stem.lower()

    if re.fullmatch(r"jemh1(0[1-9]|1[0-4])", stem):
        return "NORMAL_CHAPTER"

    if stem in {"jemh1a1", "jemh1a2"}:
        return "ADDITIONAL_CHAPTER"

    if stem == "jemh1an":
        return "ANSWERS"

    if stem == "jemh1ps":
        return "PRELIMINARY"

    raise ValueError(f"Unknown document: {filename}")


# ============================================================
# CHAPTER NUMBER
# ============================================================

def extract_chapter_number(filename: str) -> int | None:
    stem = Path(filename).stem.lower()

    match = re.fullmatch(r"jemh1(0[1-9]|1[0-4])", stem)

    if match:
        return int(match.group(1))

    return None


# ============================================================
# STABLE DOCUMENT ID
# ============================================================

def build_document_id(filename: str) -> str:
    stem = Path(filename).stem.upper()
    return f"NCERT_X_MATH_{stem}"


# ============================================================
# TITLE CANDIDATE
# ============================================================

def extract_title_candidate(pdf_path: Path) -> str | None:
    try:
        with pymupdf.open(pdf_path) as doc:

            if len(doc) == 0:
                return None

            text_blocks = doc[0].get_text("blocks", sort=True)

        lines = [
            line.strip()
            for block in text_blocks
            for line in block[4].splitlines()
            if line.strip()
        ]

        if not lines:
            return None

        # Chapter titles in these PDFs are uppercase display text. The first
        # extracted line is often a running header such as "MATHEMATICS" or a
        # printed page number, so it is not a reliable title.
        title_lines = []
        for line in lines[:20]:
            is_display_title = (
                len(line) >= 3
                and line[0].isalpha()
                and line == line.upper()
                and any(character.isalpha() for character in line)
                and line != "MATHEMATICS"
            )
            if is_display_title:
                title_lines.append(line)
                continue
            if title_lines:
                break

        return " ".join(title_lines) if title_lines else None

    except Exception as e:
        print(f"WARNING: Could not extract title from {pdf_path.name}: {e}")
        return None


# ============================================================
# BUILD DOCUMENT RECORD
# ============================================================

def build_document_record(pdf_path: Path) -> dict:

    filename = pdf_path.name

    document_type = classify_document(filename)

    chapter_number = extract_chapter_number(filename)

    document_id = build_document_id(filename)

    with pymupdf.open(pdf_path) as doc:
        page_count = len(doc)

    title = extract_title_candidate(pdf_path)

    source_role = {
        "NORMAL_CHAPTER": "syllabus_chapter",
        "ADDITIONAL_CHAPTER": "additional_content",
        "ANSWERS": "answer_key",
        "PRELIMINARY": "preliminary_material",
    }[document_type]

    return {
        "document_id": document_id,
        "filename": filename,
        "document_type": document_type,
        "chapter_number": chapter_number,
        "title": title,
        "page_count": page_count,
        "source_role": source_role,
    }


# ============================================================
# VALIDATE RAW FILES
# ============================================================

def validate_raw_files():

    if not RAW_DIR.exists():
        raise FileNotFoundError(
            f"Raw directory does not exist:\n{RAW_DIR}"
        )

    missing = []

    for filename in EXPECTED_FILES:

        if not (RAW_DIR / filename).exists():
            missing.append(filename)

    if missing:

        print("\nERROR: Missing PDF files:\n")

        for filename in missing:
            print(f"  {filename}")

        raise SystemExit(1)


# ============================================================
# VALIDATE MANIFEST
# ============================================================

def validate_manifest(manifest: dict):

    documents = manifest["documents"]

    # Must have exactly 18 documents
    assert len(documents) == 18, (
        f"Expected 18 documents, found {len(documents)}"
    )

    expected_types = {
        **{
            f"jemh1{chapter:02d}.pdf": "NORMAL_CHAPTER"
            for chapter in range(1, 15)
        },
        "jemh1a1.pdf": "ADDITIONAL_CHAPTER",
        "jemh1a2.pdf": "ADDITIONAL_CHAPTER",
        "jemh1an.pdf": "ANSWERS",
        "jemh1ps.pdf": "PRELIMINARY",
    }

    seen_ids = set()
    seen_files = set()

    for document in documents:

        required_fields = [
            "document_id",
            "filename",
            "document_type",
            "chapter_number",
            "title",
            "page_count",
            "source_role",
        ]

        for field in required_fields:
            assert field in document, (
                f"Missing field '{field}' in {document}"
            )

        document_id = document["document_id"]
        filename = document["filename"]

        # No duplicate IDs
        assert document_id not in seen_ids, (
            f"Duplicate document_id: {document_id}"
        )

        # No duplicate filenames
        assert filename not in seen_files, (
            f"Duplicate filename: {filename}"
        )

        seen_ids.add(document_id)
        seen_files.add(filename)

        # Correct classification
        assert filename in expected_types, (
            f"Unexpected file: {filename}"
        )

        assert document["document_type"] == expected_types[filename], (
            f"Wrong classification for {filename}"
        )

        # Valid page count
        assert isinstance(document["page_count"], int), (
            f"Invalid page count for {filename}"
        )

        assert document["page_count"] > 0, (
            f"Invalid page count for {filename}"
        )

    print("\nMANIFEST VALIDATION PASSED")


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("NCERT CORPUS MANIFEST GENERATOR")
    print("=" * 70)

    print(f"\nProject root:")
    print(PROJECT_ROOT)

    print(f"\nRaw directory:")
    print(RAW_DIR)

    # --------------------------------------------------------
    # Check PDFs
    # --------------------------------------------------------

    validate_raw_files()

    print("\nAll 18 expected PDFs found.")

    # --------------------------------------------------------
    # Build records
    # --------------------------------------------------------

    documents = []

    for filename in EXPECTED_FILES:

        pdf_path = RAW_DIR / filename

        record = build_document_record(pdf_path)

        documents.append(record)

        print(
            f"{filename:12} | "
            f"{record['document_type']:18} | "
            f"chapter={str(record['chapter_number']):>2} | "
            f"pages={record['page_count']:>3} | "
            f"title={record['title']}"
        )

    # --------------------------------------------------------
    # Build manifest
    # --------------------------------------------------------

    manifest = {
        "corpus": "NCERT Class X Mathematics",
        "manifest_version": "1.0",
        "document_count": len(documents),
        "documents": documents,
    }

    # --------------------------------------------------------
    # Save manifest
    # --------------------------------------------------------

    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)

    with MANIFEST_PATH.open("w", encoding="utf-8") as f:
        json.dump(
            manifest,
            f,
            indent=2,
            ensure_ascii=False,
        )

    print("\nManifest created:")
    print(MANIFEST_PATH)

    # --------------------------------------------------------
    # Validate manifest
    # --------------------------------------------------------

    validate_manifest(manifest)

    print("\n" + "=" * 70)
    print("STAGE 2 COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
