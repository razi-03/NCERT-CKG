# NCERT CKG Extraction Pipeline

## Overview

This repository implements an auditable Knowledge Graph (CKG) creation pipeline for the supplied NCERT Class X Mathematics corpus.

The current scope is deliberately limited to the **document extraction and CKG construction problem**. It does **not** implement RAG, hybrid retrieval, reranking, question answering, tutoring, or a chatbot.

The central objective is:

> Reliably transform a messy mathematical textbook into a structured, auditable, scalable knowledge graph while preserving traceability to the original textbook.

---

## Pipeline

```text
NCERT PDF Corpus
        |
        v
Corpus Classification / Manifest
        |
        v
Document Parsing
        |
        v
DocumentBlocks
(text, geometry, reading order, confidence)
        |
        v
Extraction Validation
        |
        +--------------------+
        |                    |
        v                    v
   Accepted Blocks      Review Queue
                             |
                             v
                    Math OCR / Manual Review
        |
        v
Ontology-Aware Entity Extraction
        |
        v
Canonicalization
        |
        v
Relationship Construction
        |
        v
Provenance Attachment
        |
        v
Graph Validation
        |
        v
CKG Dataset
        |
        v
Evaluation
```

---

# 1. Project Objectives

The pipeline is designed to demonstrate that the NCERT corpus can be transformed into a structured CKG while addressing real document-extraction problems.

The system preserves:

- document identity
- page identity
- block identity
- geometric location
- reading order
- mathematical content
- extraction confidence
- semantic entity identity
- relationship evidence
- provenance
- validation results

The design therefore separates:

```text
Document Parsing
        |
        v
Information Extraction
        |
        v
Knowledge Representation
        |
        v
Graph Validation
        |
        v
Evaluation
```

---

# 2. Corpus

The supplied corpus contains 18 PDFs.

## Normal chapters

```text
jemh101.pdf
jemh102.pdf
jemh103.pdf
jemh104.pdf
jemh105.pdf
jemh106.pdf
jemh107.pdf
jemh108.pdf
jemh109.pdf
jemh110.pdf
jemh111.pdf
jemh112.pdf
jemh113.pdf
jemh114.pdf
```

These are classified as:

```text
NORMAL_CHAPTER
```

## Additional chapters

```text
jemh1a1.pdf
jemh1a2.pdf
```

These are classified as:

```text
ADDITIONAL_CHAPTER
```

They are represented in the CKG separately from the normal syllabus chapters.

## Answer source

```text
jemh1an.pdf
```

Classification:

```text
ANSWERS
```

The answer source is included in the CKG so that exercises and their corresponding answers can eventually be connected.

## Preliminary material

```text
jemh1ps.pdf
```

Classification:

```text
PRELIMINARY
```

This source is retained as metadata/indexing material and is excluded from normal semantic CKG extraction.

---

# 3. Current Implementation Status

The current baseline pipeline implements:

- corpus manifest generation
- corpus classification
- DocumentBlock generation
- extraction validation
- extraction review queue
- ontology-aware entity extraction
- conservative canonicalization
- provenance-aware relationship construction
- graph validation
- CKG JSON generation

The current implementation intentionally does not implement:

- RAG
- FAISS
- BM25
- hybrid retrieval
- reranking
- query answering
- tutor generation
- chatbot functionality

---

# 4. Current Results

Current reported pipeline results:

```text
Corpus:
18 PDFs

Semantic-source pages:
262

CKG nodes:
10,417

Provenance-aware edges:
13,757

Semantic nodes:
1,682

Semantic nodes with provenance:
1,682 / 1,682

Provenance coverage:
100%

Extraction review findings:
1,081
```

The 1,081 review findings are not silently discarded. They are routed into an extraction review workflow.

Identified categories include:

- fragmented mathematical formula structure
- private-use mathematical glyphs
- false figure detection
- other extraction uncertainty requiring mathematical OCR or manual review

These findings are treated as evidence about the limitations of baseline PDF extraction rather than as silently accepted output.

---

# 5. DocumentBlock Layer

DocumentBlocks are the intermediate representation between the PDF and the semantic CKG.

A DocumentBlock contains the equivalent of:

```text
document_id
page
block_id
type
bbox
reading_order
text
latex
image_ref
confidence
```

Conceptually:

```json
{
  "document_id": "NCERT_X_MATH_JEMH106",
  "page": 1,
  "block_id": "p01_b07",
  "type": "formula",
  "bbox": [x1, y1, x2, y2],
  "reading_order": 7,
  "text": "...",
  "latex": "...",
  "image_ref": null,
  "confidence": 0.91
}
```

Not every field is necessarily populated for every block type.

The DocumentBlock layer exists so that downstream semantic extraction does not operate directly on uncontrolled PDF text.

---

# 6. Why Geometry Is Preserved

Mathematical textbooks contain:

- equations
- figures
- captions
- tables
- multi-column structures
- side-by-side visual content
- headings
- examples
- proofs

Plain text extraction can destroy the relationship between these elements.

Bounding boxes and reading order therefore remain part of the intermediate representation.

The original source location can be reconstructed through:

```text
CKG Entity
    |
    v
DocumentBlock
    |
    v
Page
    |
    v
Bounding Box
    |
    v
Original PDF
```

---

# 7. Ontology

The current ontology includes:

```text
Curriculum
Book
Chapter
Section
Concept
Definition
Formula
Theorem
Proof
Example
Exercise
LearningOutcome
Misconception
Representation
Page
DocumentBlock
```

The purpose of the ontology is to distinguish different semantic roles rather than treating every extracted text span as the same type of entity.

For example:

```text
Concept
    |
    +-- defined_by --> Definition
    |
    +-- has_formula --> Formula
    |
    +-- evidenced_by --> DocumentBlock
```

A Concept represents the mathematical idea being taught.

A Definition represents a statement that defines a concept.

A Formula represents a mathematical expression associated with a concept.

A Theorem represents a mathematical result.

A Proof represents reasoning supporting a theorem or mathematical claim.

An Exercise represents a student-facing problem or task.

A DocumentBlock remains the source-level representation from which semantic entities obtain evidence.

---

# 8. Relationships

Current relationship types include:

```text
contains
evidenced_by
has_formula
defined_by
depends_on
uses
tests_concept
```

Relationships are created according to semantic extraction rules rather than simple textual proximity.

For example:

```text
Chapter
    |
    +-- contains --> Section

Concept
    |
    +-- defined_by --> Definition

Concept
    |
    +-- has_formula --> Formula

Exercise
    |
    +-- tests_concept --> Concept
```

Each relationship is intended to remain traceable to supporting source evidence.

---

# 9. Prerequisite Relationships

Prerequisite reasoning is treated separately from textbook ordering.

The system does **not** assume:

```text
Chapter A appears before Chapter B
        =>
Concept A is a prerequisite of Concept B
```

A prerequisite relationship must instead be supported by conceptual dependency evidence or an explicit inference procedure.

Prerequisite relationships are also cycle-checked during graph validation.

For example, this is invalid:

```text
A -> prerequisite_for -> B
B -> prerequisite_for -> C
C -> prerequisite_for -> A
```

---

# 10. Provenance

Provenance is a first-class part of the graph.

Every semantic node is required to have source evidence.

The intended provenance chain is:

```text
Semantic Entity
      |
      v
DocumentBlock
      |
      v
Page
      |
      v
Bounding Box
      |
      v
Original PDF
```

Relationship provenance is also retained where applicable.

For inferred relationships, metadata should include information equivalent to:

```text
evidence
inference_method
confidence
```

This allows a graph statement to be audited instead of being treated as an unexplained model output.

---

# 11. Validation

Graph validation is a separate stage.

Current validation includes:

## Semantic evidence

Every semantic node must have source evidence.

```text
Semantic Node
      |
      +-- evidenced_by --> Existing DocumentBlock
```

## Evidence existence

Every referenced evidence block must actually exist.

## Relationship integrity

Every relationship endpoint must reference an existing node.

## Prerequisite cycle detection

The prerequisite graph is checked for cycles.

## Provenance coverage

Semantic-node provenance coverage is measured explicitly.

The current reported result is:

```text
1,682 / 1,682 semantic nodes have provenance
```

---

# 12. Extraction Validation

Baseline extraction is intentionally not assumed to be perfect.

The pipeline records extraction failures such as:

```text
Formula fragmentation
Mathematical glyph corruption
Figure false positives
Reading-order problems
Other low-confidence extraction cases
```

These are routed to a review queue instead of being silently treated as correct.

The review process is intended to support:

```text
Baseline extraction
        |
        v
Validation
        |
        +---- valid ------> accept
        |
        +---- invalid ----> review/reprocess
                              |
                              v
                    Math OCR / Manual Review
```

---

# 13. Parser Strategy

## Current parser

The current development implementation uses a baseline PDF extraction approach with deterministic validation.

Its purpose is to establish:

- reproducible document extraction
- a stable DocumentBlock representation
- measurable failure modes
- an extraction review queue

## Planned parser hierarchy

The next extraction upgrade is:

```text
Primary:
MinerU

Fallback:
PaddleOCR-VL / math OCR

Final fallback:
Manual review for unresolved high-value mathematical content
```

MinerU and PaddleOCR-VL/math OCR are not currently installed in the development environment.

The current baseline should therefore be considered an operational extraction baseline, not the final mathematical-layout extraction system.

---

# 14. Evaluation Methodology

Evaluation is separated from validation.

## Validation asks:

```text
Does the graph satisfy structural rules?
```

Examples:

- evidence exists
- relationship endpoints exist
- prerequisite graph is acyclic

## Evaluation asks:

```text
Is the extracted information actually correct?
```

Evaluation areas include:

### Document extraction

- block detection
- reading order
- text accuracy
- formula structure
- figure detection
- table detection
- confidence behaviour

### CKG extraction

- concept classification
- definition classification
- formula classification
- theorem/proof extraction
- exercise extraction
- canonicalization
- relationship correctness
- prerequisite correctness
- provenance completeness

### Manual evaluation

Mathematical content that cannot be reliably evaluated through deterministic rules should be sampled and reviewed manually.

---

# 15. TDD / Testing Strategy

Tests should be organized around deterministic invariants and representative extraction cases.

Examples:

```text
test_manifest_classification
test_document_block_schema
test_unique_block_ids
test_relationship_endpoint_integrity
test_semantic_node_provenance
test_prerequisite_cycle_detection
test_preliminary_exclusion
test_additional_chapter_classification
test_answer_source_classification
```

Mathematical extraction tests should contain known difficult examples and expected outputs.

The purpose is to prevent later parser or extraction changes from silently degrading the CKG.

---

# 16. Repository Structure

A recommended project structure is:

```text
ncert-ckg/
|
├── data/
│   ├── raw/
│   ├── manifests/
│   └── document_blocks/
|
├── src/
│   ├── ingestion/
│   ├── parsing/
│   ├── schemas/
│   ├── validation/
│   ├── ontology/
│   ├── extraction/
│   ├── canonicalization/
│   ├── relationships/
│   ├── provenance/
│   └── graph_validation/
|
├── tests/
|
├── evaluation/
|
├── notebooks/
|
├── outputs/
|
├── README.md
└── requirements.txt
```

---

# 17. Reproducibility

The pipeline should be executable from a clean environment.

Important requirements:

1. Corpus files remain immutable.
2. Generated artifacts are written outside `data/raw/`.
3. Configuration is explicit.
4. Parser versions are recorded.
5. Model/OCR versions are recorded when integrated.
6. Validation results are persisted.
7. Evaluation outputs are reproducible.

---

# 18. Current Limitations

The current implementation has a working baseline extraction and validation pipeline, but mathematical extraction is not yet fully resolved.

Known limitations:

```text
1. MinerU is not yet integrated.
2. PaddleOCR-VL/math OCR is not yet integrated.
3. Baseline extraction produces a significant review queue.
4. Mathematical glyph normalization still requires dedicated handling.
5. Formula reconstruction requires stronger layout-aware extraction.
6. Figure detection requires improved filtering of decorative/full-page images.
```

The presence of the review queue is intentional. Uncertain mathematical content should not be silently promoted into trusted semantic knowledge.

---

# 19. Next Implementation Stage

The next stage is to replace the baseline extraction path with a layout-aware parser hierarchy:

```text
NCERT PDF
    |
    v
MinerU
    |
    v
DocumentBlocks
    |
    v
Deterministic validation
    |
    +---- valid ------> accept
    |
    +---- invalid ----> mathematical OCR / review
```

The next engineering objective is therefore **extraction quality**, not RAG.

---

# 20. Definition of Success

The project is successful when the pipeline can demonstrate:

```text
PDF
  |
  v
Accurate document structure
  |
  v
Validated DocumentBlocks
  |
  v
Correct semantic entities
  |
  v
Correctly justified relationships
  |
  v
Complete provenance
  |
  v
Validated graph
  |
  v
Measurable evaluation
```

The final CKG should not merely contain thousands of nodes.

Every important graph object should answer:

```text
What is this?
Why does it exist?
What source supports it?
Where exactly is that source?
How was the relationship created?
How confident is the inference?
Did deterministic validation pass?
```

That is the standard this pipeline is designed to satisfy.
