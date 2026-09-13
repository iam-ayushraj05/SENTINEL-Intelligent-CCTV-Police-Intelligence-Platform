import logging
import time
from typing import Any, List, Optional
import numpy as np

from ai.sentinel_ai.config.settings import ai_settings
from ai.sentinel_ai.events.schema import EventType, SentinelAIEvent
from ai.sentinel_ai.scheduler.resource_manager import resource_manager

logger = logging.getLogger("sentinel.ai.vehicle_detector")

# COCO vehicle class IDs
VEHICLE_CLASSES = {
    1: "bicycle",
    2: "car",
    3: "motorcycle",
    5: "bus",
    7: "truck",
}


class VehicleDetector:
    """
    Ultralytics YOLO vehicle detector returning normalized VEHICLE_DETECTED events.
    """

    def __init__(self, model_path: str = "yolo11n.pt"):
        self.model_name = "vehicle_yolo"
        self.model_version = "1.0.0"
        self.model_path = model_path
        self.model = None

        try:
            from ultralytics import YOLO
            self.model = YOLO(model_path)
            resource_manager.register_model(self.model_name, self.model, version=self.model_version)
            logger.info("Loaded VehicleDetector using %s", model_path)
        except Exception as e:
            logger.warning("Failed to load YOLO model for VehicleDetector (%s): %s", model_path, e)

    def detect(
        self,
        frame: np.ndarray,
        camera_id: str = "cam_default",
        track_map: Optional[dict] = None,
    ) -> List[SentinelAIEvent]:
        if self.model is None or frame is None:
            return []

        start_time = time.time()
        events: List[SentinelAIEvent] = []

        try:
            results = self.model.predict(
                frame,
                conf=ai_settings.AI_DETECTION_CONFIDENCE,
                classes=list(VEHICLE_CLASSES.keys()),
                verbose=False,
            )[0]

            if results.boxes is not None:
                for idx, box in enumerate(results.boxes):
                    conf = float(box.conf[0].item())
                    cls_id = int(box.cls[0].item())
                    vehicle_type = VEHICLE_CLASSES.get(cls_id, "vehicle")
                    x1, y1, x2, y2 = [float(v) for v in box.xyxy[0].tolist()]
                    track_id = str(track_map.get(idx)) if track_map and idx in track_map else None

                    event = SentinelAIEvent(
                        event_type=EventType.VEHICLE_DETECTED,
                        camera_id=camera_id,
                        track_id=track_id,
                        class_name=vehicle_type,
                        confidence=round(conf, 4),
                        bounding_box=[round(x1, 1), round(y1, 1), round(x2, 1), round(y2, 1)],
                        model_name=self.model_name,
                        model_version=self.model_version,
                        status="DETECTED",
                        requires_human_review=False,
                        metadata={"class_id": cls_id},
                    )
                    events.append(event)

            latency_ms = (time.time() - start_time) * 1000.0
            resource_manager.record_inference(self.model_name, latency_ms, success=True)
        except Exception as e:
            logger.exception("Error in VehicleDetector inference: %s", e)
            resource_manager.record_inference(self.model_name, 0.0, success=False)

        return events
