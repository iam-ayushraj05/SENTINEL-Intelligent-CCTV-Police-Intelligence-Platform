from typing import Any
from ai.anpr.ocr import PlateOCR


class PlateDetector:
    """
    ANPR Pipeline: Vehicle Detection -> Plate Crop -> OCR -> Normalization -> Sighting Record
    """

    def __init__(self):
        self.ocr_engine = PlateOCR()

    async def process_vehicle_crop(self, vehicle_crop: Any) -> dict[str, Any] | None:
        ocr_result = await self.ocr_engine.read_plate(vehicle_crop)
        return {
            "plate_number": ocr_result["raw_text"],
            "normalized_plate": ocr_result["normalized_plate"],
            "ocr_confidence": ocr_result["ocr_confidence"],
        }
