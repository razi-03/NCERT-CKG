"""The page-level intermediate representation used by document parsers."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal


BlockType = Literal[
    "document_title",
    "chapter_title",
    "section_heading",
    "subsection_heading",
    "paragraph",
    "formula",
    "theorem",
    "proof",
    "example",
    "exercise",
    "figure",
    "table",
    "caption",
    "list",
    "header",
    "footer",
    "unknown",
]


@dataclass(frozen=True)
class DocumentBlock:
    """One extracted object from one PDF page.

    ``page`` is one-based and refers to the PDF page index, not the printed
    textbook page number. Coordinates use the PDF coordinate space.
    """

    document_id: str
    page: int
    block_id: str
    type: BlockType
    bbox: list[float]
    reading_order: int
    text: str | None = None
    latex: str | None = None
    image_ref: str | None = None
    confidence: float = 1.0

    def __post_init__(self) -> None:
        if self.page < 1:
            raise ValueError("page must be one-based")
        if len(self.bbox) != 4:
            raise ValueError("bbox must contain [x1, y1, x2, y2]")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serializable representation."""
        return asdict(self)
