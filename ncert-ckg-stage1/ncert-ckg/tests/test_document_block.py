import unittest

from schemas.document_block import DocumentBlock


class DocumentBlockTests(unittest.TestCase):
    def test_serializes_required_fields(self) -> None:
        block = DocumentBlock(
            document_id="NCERT_X_MATH_JEMH101",
            page=1,
            block_id="jemh101_p001_b01",
            type="paragraph",
            bbox=[1.0, 2.0, 3.0, 4.0],
            reading_order=1,
            text="Example text",
        )

        self.assertEqual(block.to_dict()["block_id"], "jemh101_p001_b01")

    def test_rejects_invalid_confidence(self) -> None:
        with self.assertRaises(ValueError):
            DocumentBlock(
                document_id="id",
                page=1,
                block_id="block",
                type="paragraph",
                bbox=[1, 2, 3, 4],
                reading_order=1,
                confidence=1.1,
            )


if __name__ == "__main__":
    unittest.main()
