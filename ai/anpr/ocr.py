import logging
from typing import Any
from ai.anpr.normalizer import normalize_plate_number

logger = logging.getLogger("sentinel.ai.anpr")


class PlateOCR:
    """
    OCR Engine abstraction for license plate character extraction.
    Integrates EasyOCR / PyTesseract with safe normalization fallback.
    """

    def __init__(self):
        self.reader = None
        try:
            import easyocr
            self.reader = easyocr.Reader(["en"], gpu=False)
            logger.info("Loaded EasyOCR engine for ANPR")
        except Exception:
            logger.info("EasyOCR not installed or initialized; using Tesseract/pattern fallback")

    async def read_plate(self, plate_crop: Any) -> dict[str, Any]:
        if plate_crop is None:
            return {"raw_text": "", "normalized_plate": "", "ocr_confidence": 0.0}

        raw_text = ""
        confidence = 0.0

        if self.reader is not None:
            try:
                import asyncio
                results = await asyncio.to_thread(self.reader.readtext, plate_crop)
                if results:
                    best = max(results, key=lambda res: res[2])
                    raw_text = str(best[1])
                    confidence = float(best[2])
            except Exception as exc:
                logger.debug("EasyOCR processing error: %s", exc)

        if not raw_text:
            try:
                import pytesseract
                import asyncio
                raw_text = await asyncio.to_thread(pytesseract.image_to_string, plate_crop, config="--psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
                confidence = 0.85 if raw_text.strip() else 0.0
            except Exception:
                pass

        normalized = normalize_plate_number(raw_text)
        return {
            "raw_text": raw_text.strip(),
            "normalized_plate": normalized,
            "ocr_confidence": round(confidence, 4) if confidence > 0 else (0.88 if normalized else 0.0),
        }
