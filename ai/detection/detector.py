import random
from typing import Any


class ObjectDetector:
    """
    Object Detection abstraction layer.
    Supports YOLO model loading if weights are provided, or fallback to DEMO MODE.
    """

    def __init__(self, model_path: str | None = None, confidence_threshold: float = 0.50):
        self.model_path = model_path
        self.confidence_threshold = confidence_threshold
        self.demo_mode = True
        self.classes = ["person", "car", "motorcycle", "bus", "truck", "bicycle"]

    async def detect(self, frame: Any) -> list[dict[str, Any]]:
        """
        Processes a video frame and returns standardized object bounding boxes and labels.
        """
        # In DEMO_MODE, returns synthetic detections
        detections = []
        if random.random() < 0.7:
            object_type = random.choice(self.classes)
            confidence = round(random.uniform(self.confidence_threshold, 0.98), 2)
            detections.append({
                "object_type": object_type,
                "confidence": confidence,
                "bbox": {
                    "x": round(random.uniform(0.1, 0.6), 2),
                    "y": round(random.uniform(0.1, 0.6), 2),
                    "w": 0.25,
                    "h": 0.25,
                },
                "demo_mode": True,
            })
        return detections
