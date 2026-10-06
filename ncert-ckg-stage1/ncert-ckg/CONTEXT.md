# NCERT Curriculum Knowledge Graph

This context turns NCERT mathematics source material into an auditable
curriculum knowledge graph. It distinguishes physical document evidence from
the mathematical claims derived from that evidence.

## Language

**DocumentBlock**:
One physical object extracted from a PDF page, with location and extraction
confidence. It is evidence, not mathematical meaning.
_Avoid_: chunk, knowledge node

**Semantic node**:
A curriculum or mathematical object such as a Concept, Definition, Formula,
or Exercise represented in the graph.
_Avoid_: block, PDF entity

**Evidence**:
A link from a semantic claim to one or more DocumentBlocks in the source PDF.
_Avoid_: citation, reference (when the exact block is meant)

**Prerequisite**:
A justified conceptual dependency; it is never inferred merely from textbook
order.
_Avoid_: previous chapter, sequence edge

**Additional chapter**:
An appendix-like mathematical chapter outside the fourteen normal syllabus
chapters. It remains semantic CKG content.

**Preliminary material**:
Front matter retained as document metadata or table-of-contents information,
but excluded from semantic CKG extraction.
