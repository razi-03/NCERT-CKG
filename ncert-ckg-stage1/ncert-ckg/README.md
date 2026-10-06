# NCERT CKG

Knowledge graph pipeline for building a trustworthy structured representation of NCERT mathematics textbooks.

## Current stage

The project now implements a provenance-first CKG pilot: extraction validation,
ontology-aware rule extraction, conservative canonicalization, relationship
creation, and graph validation. It does not implement RAG or a chatbot.

The `data/raw/` directory is reserved for immutable source PDFs. Generated and derived data belongs in the appropriate downstream directories.

## Pipeline

RAW → PARSED → SEMANTIC → GRAPH

## Baseline extraction

From the project root, first generate the manifest:

```powershell
python src/ingestion/build_manifest.py
```

Then generate one page of DocumentBlocks:

```powershell
$env:PYTHONPATH = "src"
python src/parsing/baseline_parser.py jemh101.pdf --page 1
```

Generated JSON is written beneath `data/document_blocks/`; extracted embedded
images are stored beside the page output and referenced by `image_ref`.

## CKG pilot

The CKG builder accepts any generated DocumentBlocks. Generate a bounded,
reproducible pilot for every semantic source document (normal chapters,
additional chapters, and answers; not preliminary material):

```powershell
$env:PYTHONPATH = "src"
python src/ingestion/run_extraction.py --limit-pages 1
python src/extraction/build_ckg.py
```

This writes `data/ckg/ncert_x_mathematics.json` and the deterministic review
queue `evaluation/extraction_review_queue.csv`. The latter directs unreliable
formula and figure extraction to math OCR/manual review; no low-confidence
content is silently treated as correct.

`jemh1an.pdf` is included as an answer-key source. `jemh1ps.pdf` is represented
only as preliminary metadata and never contributes semantic nodes. Appendix
documents are Chapters marked `is_additional: true`.
