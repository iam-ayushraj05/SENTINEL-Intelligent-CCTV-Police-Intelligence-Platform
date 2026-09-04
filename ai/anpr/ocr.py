from typing import Any
from ai.anpr.normalizer import normalize_plate_number


class PlateOCR:
    """
    OCR Engine abstraction for license plate character extraction.
    Integrates Tesseract/EasyOCR/PaddleOCR with fallback for demo.
    """

    async def read_plate(self, plate_crop: Any) -> dict[str, Any]:
        # Simulated OCR read
        raw_text = "GJ-05-CD-5678"
        normalized = normalize_plate_number(raw_text)
        return {
            "raw_text": raw_text,
            "normalized_plate": normalized,
            "ocr_confidence": 0.94,
        }
