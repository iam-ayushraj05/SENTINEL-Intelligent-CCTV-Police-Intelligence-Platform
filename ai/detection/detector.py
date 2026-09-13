import logging
from typing import Any

logger = logging.getLogger("sentinel.ai.detector")


class ObjectDetector:
    """
    Object Detection abstraction layer.
    Ultralytics adapter. The model is loaded once and returns the platform's
    normalized detection shape. A missing optional runtime never produces fake
    detections.
    """

    def __init__(self, model_path: str | None = None, confidence_threshold: float = 0.50):
        self.model_path = model_path
        self.confidence_threshold = confidence_threshold
        self.model = None
        self.demo_mode = False
        self.classes = ["person", "car", "motorcycle", "bus", "truck", "bicycle"]
        if model_path:
            try:
                from ultralytics import YOLO
                self.model = YOLO(model_path)
                logger.info("Loaded Ultralytics model: %s", model_path)
            except ImportError:
                logger.warning("Ultralytics is not installed; AI inference is unavailable")
            except Exception:
                logger.exception("Failed to load Ultralytics model: %s", model_path)

    async def detect(self, frame: Any) -> list[dict[str, Any]]:
        """
        Processes a video frame and returns standardized object bounding boxes and labels.
        """
        if frame is None or self.model is None:
            return []

        results = await self._predict(frame)
        detections: list[dict[str, Any]] = []
        for result in results:
            names = getattr(result, "names", {})
            boxes = getattr(result, "boxes", None)
            if boxes is None:
                continue
            for index in range(len(boxes)):
                confidence = float(boxes.conf[index].item())
                if confidence < self.confidence_threshold:
                    continue
                class_id = int(boxes.cls[index].item())
                object_type = names.get(class_id, str(class_id)) if isinstance(names, dict) else str(class_id)
                coordinates = [float(value) for value in boxes.xyxy[index].tolist()]
                x1, y1, x2, y2 = coordinates
                normalized_type = str(object_type).lower()
                event_type = {
                    "fight": "FIGHT_POSSIBLE",
                    "fighting": "FIGHT_POSSIBLE",
                    "accident": "POSSIBLE_ACCIDENT",
                    "vehicle_accident": "POSSIBLE_ACCIDENT",
                    "robbery": "ROBBERY_CONFIRMED",
                    "theft": "THEFT_SUSPECTED",
                    "stealing": "THEFT_SUSPECTED",
                    "suspicious_activity": "SUSPICIOUS_ACTIVITY",
                }.get(normalized_type)
                detections.append({
                    "object_type": object_type,
                    "confidence": round(confidence, 4),
                    "bbox": {"x1": x1, "y1": y1, "x2": x2, "y2": y2},
                    "class_id": class_id,
                    "event_type": event_type,
                })
        return detections

    async def _predict(self, frame: Any) -> list[Any]:
        """Run blocking model inference away from the event loop."""
        import asyncio
        return await asyncio.to_thread(
            self.model.predict,
            source=frame,
            conf=self.confidence_threshold,
            verbose=False,
        )
