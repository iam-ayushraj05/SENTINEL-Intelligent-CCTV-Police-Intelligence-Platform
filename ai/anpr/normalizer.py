import re


def normalize_plate_number(raw_ocr_text: str) -> str:
    """
    Normalizes vehicle license plate OCR text.
    Handles common Indian / State format variations and OCR misread character swaps:
    - O -> 0 in numeric positions
    - I/L -> 1 in numeric positions
    - Z -> 2
    - S -> 5
    - B -> 8
    - Strip whitespace, hyphens, special chars
    """
    if not raw_ocr_text:
        return ""

    clean = re.sub(r"[^A-Za-z0-9]", "", raw_ocr_text).upper()

    # If format fits standard state plate (e.g. GJ01AB1234):
    if len(clean) >= 8:
        state_code = clean[:2]
        district_num = clean[2:4]
        series = clean[4:-4]
        digits = clean[-4:]

        # Correct district digits
        district_num = district_num.replace("O", "0").replace("I", "1").replace("Z", "2").replace("S", "5").replace("B", "8")
        # Correct final 4 digits
        digits = digits.replace("O", "0").replace("I", "1").replace("Z", "2").replace("S", "5").replace("B", "8")

        return f"{state_code}{district_num}{series}{digits}"

    return clean
