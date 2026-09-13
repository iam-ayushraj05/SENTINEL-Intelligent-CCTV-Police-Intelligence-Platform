import re
from typing import Optional


class ANPRNormalizer:
    """
    Normalizes OCR license plate text:
    - Uppercases characters
    - Removes invalid whitespace, symbols, and country band artifacts (e.g. EU "RO" strip)
    - Preserves low confidence without fabricating digits
    """

    @staticmethod
    def normalize_plate(raw_ocr: str) -> str:
        if not raw_ocr:
            return ""

        # Uppercase and strip whitespace/special chars except alphanumeric
        cleaned = re.sub(r"[^A-Z0-9]", "", raw_ocr.upper())

        # Strip EU country prefix if extraneous
        if cleaned.startswith("RO") and len(cleaned) > 6:
            cleaned = cleaned[2:]

        return cleaned

    @staticmethod
    def is_valid_plate(normalized: str) -> bool:
        # Generic length check: 4 to 12 alphanumeric characters
        return bool(re.match(r"^[A-Z0-9]{4,12}$", normalized))
